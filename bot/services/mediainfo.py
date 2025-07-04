# /bot/services/mediainfo.py
import json
import logging
import tempfile
from pathlib import Path

from pymediainfo import MediaInfo
from pyrogram import Client
from pyrogram.types import Message

logger = logging.getLogger(__name__)

CHUNK_SIZE_BYTES = 10 * 1024 * 1024 # 10MB

async def get_media_info(client: Client, message: Message) -> dict | None:
    """
    Descarga un chunk de un archivo usando el motor Pyrogram (sin límite de tamaño)
    y lo analiza con MediaInfo.
    """
    media = message.video or message.document
    temp_dir = Path(tempfile.gettempdir())
    temp_path = temp_dir / media.file_name

    logger.info(f"Iniciando stream de {media.file_name} para MediaInfo...")
    
    try:
        # Usamos client.stream_media para descargar el chunk
        with open(temp_path, "wb") as f:
            bytes_downloaded = 0
            async for chunk in client.stream_media(message, limit=10):
                f.write(chunk)
                bytes_downloaded += len(chunk)
                if bytes_downloaded >= CHUNK_SIZE_BYTES:
                    break
        
        logger.info(f"Chunk descargado en: {temp_path}. Analizando...")
        
        media_info_str = MediaInfo.parse(temp_path, output="JSON")
        data = json.loads(media_info_str)
        
        logger.info("Análisis de MediaInfo completado.")
        return data

    except Exception as e:
        logger.error(f"Error en get_media_info: {e}", exc_info=True)
        return None
    finally:
        # Nos aseguramos de limpiar el archivo temporal
        if temp_path.exists():
            temp_path.unlink()