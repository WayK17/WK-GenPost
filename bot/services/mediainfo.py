# /bot/services/mediainfo.py
import json
import logging
import tempfile
import asyncio

from pymediainfo import MediaInfo
from telegram import Video, Document

# Usamos el mismo logger que en main
logger = logging.getLogger(__name__)

# Definimos cuántos megabytes descargar para el análisis
CHUNK_SIZE_MB = 10
CHUNK_SIZE_BYTES = CHUNK_SIZE_MB * 1024 * 1024

async def get_media_info(file: Video | Document) -> dict:
    """
    Descarga una parte de un archivo de video/documento, lo analiza con
    MediaInfo y devuelve los metadatos como un diccionario.
    """
    with tempfile.NamedTemporaryFile(suffix=f"_{file.file_name}") as temp_file:
        logger.info(f"Descargando chunk de {CHUNK_SIZE_MB}MB para el archivo: {file.file_name}")
        
        # Descargamos el chunk del archivo
        await file.download_to_drive(custom_path=temp_file.name, read_timeout=60, write_timeout=60)
        
        logger.info(f"Chunk descargado en: {temp_file.name}. Analizando con MediaInfo...")

        try:
            # Analizamos el archivo temporal y pedimos la salida en formato JSON
            media_info = MediaInfo.parse(temp_file.name, output="JSON")
            # Convertimos el string JSON a un diccionario de Python
            data = json.loads(media_info)
            logger.info("Análisis de MediaInfo completado con éxito.")
            return data
            
        except Exception as e:
            logger.error(f"Error al analizar el archivo con MediaInfo: {e}")
            return None