# /bot/services/tmdb.py

import httpx
import logging
from difflib import SequenceMatcher
from .. import config

logger = logging.getLogger(__name__)

BASE_URL = "https://api.themoviedb.org/3"

# --- FUNCIONES DE AYUDA ---

def find_best_match(query: str, results: list) -> dict | None:
    """
    Usa un comparador de strings para encontrar el mejor resultado en una lista.
    Esto mejora drásticamente la precisión de la búsqueda.
    """
    if not results:
        return None

    best_match = None
    highest_ratio = 0.0

    # Itera sobre los resultados para encontrar el que más se parece al título original
    for result in results:
        title_key = 'title' if 'title' in result else 'name'
        if result.get(title_key):
            ratio = SequenceMatcher(None, query.lower(), result[title_key].lower()).ratio()
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = result
    
    # Solo acepta el resultado si la similitud es razonable (evita falsos positivos)
    if highest_ratio > 0.75: # Umbral de confianza del 60%
        return best_match
    
    logger.warning(f"No se encontró un resultado suficientemente bueno para '{query}'. El mejor tuvo un ratio de {highest_ratio:.2f}.")
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
    """Busca una película en TMDb con búsqueda inteligente."""
    logger.info(f"Buscando PELÍCULA en TMDb: Título='{title}', Año='{year}'")
    
    search_params = {
        "api_key": config.TMDB_API_KEY,
        "query": title,
        "language": "es-ES",
        "primary_release_year": year if year else ''
    }
    
    search_data = await fetch_from_tmdb(f"{config.TMDB_API_URL}/search/movie", search_params)
    
    if search_data and search_data.get("results"):
        best_match = find_best_match(title, search_data["results"])
        if best_match:
            movie_id = best_match['id']
            logger.info(f"Película encontrada: '{best_match['title']}' (ID: {movie_id})")
            
            # Modificación: añadir "credits" para obtener actores y director
            details_params = {"api_key": config.TMDB_API_KEY, "language": "es-ES", "append_to_response": "credits"}
            details_data = await fetch_from_tmdb(f"{config.TMDB_API_URL}/movie/{movie_id}", details_params)
            
            if details_data:
                logger.info("Detalles, créditos y géneros de la película obtenidos.")
                return details_data
    
    logger.warning(f"No se encontró la película '{title}' en TMDb.")
    return None

async def search_series(title: str, season_number: int | None, episode_number: int | None) -> dict | None:
    """Busca una serie y opcionalmente un episodio específico con búsqueda inteligente."""
    logger.info(f"Buscando SERIE en TMDb: Título='{title}', S={season_number}, E={episode_number}")
    
    # 1. Buscar la serie
    search_params = {"api_key": config.TMDB_API_KEY, "query": title, "language": "es-ES"}
    search_data = await fetch_from_tmdb(f"{config.TMDB_API_URL}/search/tv", search_params)

    if not search_data or not search_data.get("results"):
        logger.warning(f"No se encontró la serie '{title}' en TMDb.")
        return None

    best_match = find_best_match(title, search_data["results"])
    if not best_match:
        return None
        
    series_id = best_match['id']
    logger.info(f"Serie encontrada: '{best_match['name']}' (ID: {series_id})")

    # Modificación: añadir "credits" para obtener actores y director de la serie
    details_params = {"api_key": config.TMDB_API_KEY, "language": "es-ES", "append_to_response": "credits"}
    series_details = await fetch_from_tmdb(f"{config.TMDB_API_URL}/tv/{series_id}", details_params)

    # 2. Si tenemos temporada y episodio, buscamos sus detalles. SI NO, devolvemos solo la serie.
    if season_number is not None and episode_number is not None:
        logger.info(f"Buscando detalles del episodio S{season_number:02d}E{episode_number:02d}...")
        
        # Primero obtenemos los detalles de la temporada para el poster
        season_details_data = await fetch_from_tmdb(f"{config.TMDB_API_URL}/tv/{series_id}/season/{season_number}", {"api_key": config.TMDB_API_KEY, "language": "es-ES"})

        # Luego los detalles del episodio, pero los fusionaremos con los de la serie principal
        episode_details_data = await fetch_from_tmdb(f"{config.TMDB_API_URL}/tv/{series_id}/season/{season_number}/episode/{episode_number}", {"api_key": config.TMDB_API_KEY, "language": "es-ES"})

        if episode_details_data:
            # Combinamos la información para tener todo en un solo diccionario
            series_info = await fetch_from_tmdb(f"{config.TMDB_API_URL}/tv/{series_id}", {"api_key": config.TMDB_API_KEY, "language": "es-ES"})
            series_info['episode_details'] = episode_details_data
            series_info['season_poster_path'] = season_details_data.get('poster_path')
            logger.info("Detalles del episodio encontrados y combinados.")
            return series_info

        logger.warning(f"No se encontró el episodio S{season_number:02d}E{episode_number:02d}, se devolverá info de la serie.")

    # Si no se busca un episodio o no se encontró, devolvemos la información general de la serie
    series_details = await fetch_from_tmdb(f"{config.TMDB_API_URL}/tv/{series_id}", {"api_key": config.TMDB_API_KEY, "language": "es-ES"})
    return series_details