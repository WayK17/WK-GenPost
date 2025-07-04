# /bot/services/tmdb.py
import logging
import aiohttp
# Cambiamos la importación
from bot import config

logger = logging.getLogger(__name__)

BASE_URL = "https://api.themoviedb.org/3"

async def search_movie(title: str, year: int | None = None) -> dict | None:
    """
    Busca una película en TMDb por título y, opcionalmente, por año.
    """
    search_url = f"{BASE_URL}/search/movie"
    params = {
        'api_key': config.TMDB_API_KEY,
        'query': title,
        'language': 'es-ES'
    }
    # Si tenemos el año, lo añadimos a la búsqueda para máxima precisión
    if year:
        params['primary_release_year'] = year
    
    logger.info(f"Buscando PELÍCULA en TMDb con los parámetros: {params}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                if data.get("results"):
                    movie_id = data["results"][0]["id"]
                    
                    # CORRECCIÓN: Obtener detalles completos de la película incluyendo géneros
                    movie_details_url = f"{BASE_URL}/movie/{movie_id}"
                    movie_params = {'api_key': config.TMDB_API_KEY, 'language': 'es-ES'}
                    
                    async with session.get(movie_details_url, params=movie_params) as details_response:
                        details_response.raise_for_status()
                        movie_details = await details_response.json()
                        logger.info("Película encontrada en TMDb con géneros.")
                        return movie_details
                else:
                    logger.warning("No se encontraron resultados para la película.")
                    return None
    except Exception as e:
        logger.error(f"Error al conectar con TMDb para buscar película: {e}")
        return None

async def search_series(title: str, season: int, episode_number: int = None) -> dict | None:
    """
    Busca un episodio específico de una serie en TMDb.
    Si episode_number es None, busca la temporada completa.
    """
    # Paso 1: Buscar el ID de la serie
    search_tv_url = f"{BASE_URL}/search/tv"
    tv_params = {
        'api_key': config.TMDB_API_KEY,
        'query': title,
        'language': 'es-ES'
    }
    
    logger.info(f"Buscando SERIE en TMDb con los parámetros: {tv_params}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_tv_url, params=tv_params) as response:
                response.raise_for_status()
                tv_data = await response.json()
                
                if not tv_data.get("results"):
                    logger.warning("No se encontró la serie.")
                    return None
                
                series_id = tv_data["results"][0]["id"]
                
                # CORRECCIÓN: Primero obtenemos detalles completos de la serie para géneros
                series_details_url = f"{BASE_URL}/tv/{series_id}"
                series_params = {'api_key': config.TMDB_API_KEY, 'language': 'es-ES'}
                
                async with session.get(series_details_url, params=series_params) as series_response:
                    series_response.raise_for_status()
                    series_data = await series_response.json()
                
                # --- LÓGICA CORREGIDA ---
                if episode_number:
                    # Si nos dan un episodio, buscamos ese episodio
                    logger.info(f"Serie encontrada con ID: {series_id}. Buscando episodio {episode_number}...")
                    api_endpoint_url = f"{BASE_URL}/tv/{series_id}/season/{season}/episode/{episode_number}"
                else:
                    # Si no hay episodio, buscamos los detalles de la temporada completa
                    logger.info(f"Serie encontrada con ID: {series_id}. Buscando detalles de la temporada {season}...")
                    api_endpoint_url = f"{BASE_URL}/tv/{series_id}/season/{season}"

                episode_params = {'api_key': config.TMDB_API_KEY, 'language': 'es-ES'}

                async with session.get(api_endpoint_url, params=episode_params) as response:
                    response.raise_for_status()
                    episode_data = await response.json()
                    
                    # CORRECCIÓN: Combinamos los datos del episodio/temporada con los géneros de la serie
                    episode_data['genres'] = series_data.get('genres', [])
                    episode_data['series_genres'] = series_data.get('genres', [])  # Backup
                    
                    logger.info("Datos de la temporada/episodio encontrados con géneros.")
                    return episode_data

    except Exception as e:
        logger.error(f"Error al buscar episodio de serie en TMDb: {e}")
        return None