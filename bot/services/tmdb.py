# /bot/services/tmdb.py

import httpx
import logging
from difflib import SequenceMatcher
from .. import config
from .. import utils

logger = logging.getLogger(__name__)

BASE_URL = "https://api.themoviedb.org/3"

# --- FUNCIONES DE AYUDA ---

def find_best_match(query: str, results: list) -> dict | None:
    """
    Usa un comparador de strings MEJORADO con títulos limpios.
    """
    if not results:
        return None

    best_match = None
    highest_ratio = 0.0
    
    # Limpiamos el título original de la búsqueda UNA SOLA VEZ
    clean_query = utils.clean_title_for_matching(query)

    for result in results:
        title_key = 'title' if 'title' in result else 'name'
        result_title = result.get(title_key)
        
        if result_title:
            # Limpiamos el título del resultado de TMDb antes de comparar
            clean_result_title = clean_title_for_matching(result_title)
            
            ratio = SequenceMatcher(None, clean_query, clean_result_title).ratio()
            
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = result
    
    # Relajamos el umbral porque los títulos limpios son más fáciles de emparejar
    if highest_ratio > 0.8: # Umbral de confianza del 80% para títulos limpios
        return best_match
    
    logger.warning(f"No se encontró un resultado suficientemente bueno para '{query}'. El mejor tuvo un ratio de {highest_ratio:.2f} con títulos limpios.")
    return None

async def fetch_from_tmdb(url: str, params: dict) -> dict | None:
    """Función centralizada para hacer peticiones a la API de TMDb."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error al llamar a la API de TMDb: {e.response.status_code}, message='{e.response.text}', url='{e.request.url}'")
            return None
        except httpx.RequestError as e:
            logger.error(f"Error de red al conectar con TMDb: {e}")
            return None

# --- FUNCIONES PRINCIPALES ---

async def search_movie(title: str, year: int | None) -> dict | None:
    """Busca una película con reintentos y fallback a inglés."""
    logger.info(f"Buscando PELÍCULA: Título='{title}', Año='{year}'")
    
    titles_to_try = [title]
    if len(title.split()) > 2: # Si el título tiene más de 2 palabras
        titles_to_try.append(" ".join(title.split()[:2])) # Intenta con las primeras 2 palabras
    
    for title_attempt in titles_to_try:
        for lang_code, lang_name in [("es-ES", "español"), ("en-US", "inglés")]:
            logger.info(f"Intentando búsqueda en {lang_name} con título: '{title_attempt}'")
            params = {
                "api_key": config.TMDB_API_KEY, "query": title_attempt,
                "language": lang_code, "primary_release_year": year if year else ''
            }
            search_data = await fetch_from_tmdb(f"{config.TMDB_API_URL}/search/movie", params)
            if search_data and search_data.get("results"):
                best_match = find_best_match(title, search_data["results"]) # Compara siempre con el título original
                if best_match:
                    movie_id = best_match['id']
                    logger.info(f"Película encontrada en {lang_name}: '{best_match['title']}' (ID: {movie_id})")
                    details_params = {"api_key": config.TMDB_API_KEY, "language": "es-ES", "append_to_response": "credits"}
                    return await fetch_from_tmdb(f"{config.TMDB_API_URL}/movie/{movie_id}", details_params)
    
    logger.warning(f"No se encontró la película '{title}' tras todos los intentos.")
    return None

async def search_series(title: str, year: int | None, season_number: int | None, episode_number: int | None) -> dict | None:
    """Busca una serie con reintentos y fallback a inglés."""
    logger.info(f"Buscando SERIE: Título='{title}', Año='{year}', S={season_number}, E={episode_number}")

    titles_to_try = [title]
    if len(title.split()) > 2:
        titles_to_try.append(" ".join(title.split()[:2]))

    series_id = None
    for title_attempt in titles_to_try:
        for lang_code, lang_name in [("es-ES", "español"), ("en-US", "inglés")]:
            logger.info(f"Intentando búsqueda en {lang_name} con título: '{title_attempt}'")
            params = {
                "api_key": config.TMDB_API_KEY, "query": title_attempt,
                "language": lang_code, "first_air_date_year": year if year else ""
            }
            search_data = await fetch_from_tmdb(f"{config.TMDB_API_URL}/search/tv", params)
            if search_data and search_data.get("results"):
                best_match = find_best_match(title, search_data["results"])
                if best_match:
                    series_id = best_match['id']
                    logger.info(f"Serie encontrada en {lang_name}: '{best_match['name']}' (ID: {series_id})")
                    break # Salimos del bucle de idiomas
        if series_id:
            break # Salimos del bucle de intentos de título

    if not series_id:
        logger.warning(f"No se encontró la serie '{title}' tras todos los intentos.")
        return None

    # Modificación: añadir "credits" para obtener actores y director de la serie
    details_params = {"api_key": config.TMDB_API_KEY, "language": "es-ES", "append_to_response": "credits"}
    series_details = await fetch_from_tmdb(f"{config.TMDB_API_URL}/tv/{series_id}", details_params)

    if not series_details:
        logger.warning(f"Se encontró el ID de la serie, pero no se pudieron obtener los detalles.")
        return None

    # --- Lógica para añadir detalles del episodio ---
    if season_number is not None and episode_number is not None:
        logger.info(f"Buscando detalles del episodio S{season_number:02d}E{episode_number:02d}...")
        
        episode_details_data = await fetch_from_tmdb(
            f"{config.TMDB_API_URL}/tv/{series_id}/season/{season_number}/episode/{episode_number}",
            {"api_key": config.TMDB_API_KEY, "language": "es-ES"}
        )
        
        if episode_details_data:
            series_details['episode_details'] = episode_details_data
            logger.info("Detalles del episodio encontrados y combinados.")
        else:
            logger.warning(f"No se encontró el episodio S{season_number:02d}E{episode_number:02d}.")

    # Devolvemos los detalles de la serie (con o sin info del episodio)
    return series_details