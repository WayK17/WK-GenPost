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
                    logger.info("Película encontrada en TMDb.")
                    return data["results"][0]
                else:
                    logger.warning("No se encontraron resultados para la película.")
                    return None
    except Exception as e:
        logger.error(f"Error al conectar con TMDb para buscar película: {e}")
        return None

async def search_series(title: str, season: int, episode: int) -> dict | None:
    """
    Busca un episodio específico de una serie en TMDb.
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
                logger.info(f"Serie encontrada con ID: {series_id}. Buscando episodio...")

            # Paso 2: Usar el ID para buscar el episodio específico
            episode_url = f"{BASE_URL}/tv/{series_id}/season/{season}/episode/{episode}"
            episode_params = {
                'api_key': config.TMDB_API_KEY,
                'language': 'es-ES'
            }
            
            async with session.get(episode_url, params=episode_params) as response:
                response.raise_for_status()
                episode_data = await response.json()
                logger.info("Episodio encontrado.")
                return episode_data

    except Exception as e:
        logger.error(f"Error al buscar episodio de serie en TMDb: {e}")
        return None