# /bot/services/mediainfo.py
import json
import logging
import tempfile
import asyncio

from pymediainfo import MediaInfo
from telegram import Video, Document
from telegram.error import BadRequest  # Importamos el error específico

logger = logging.getLogger(__name__)

async def get_media_info(file: Video | Document) -> dict | None:
    """
    Intenta descargar una parte de un archivo para analizarlo con MediaInfo.
    Maneja elegantemente el error si el archivo es demasiado grande (>20MB).
    """
    try:
        # --- ¡AQUÍ ESTÁ EL BLINDAJE! ---
        # Intentamos obtener el objeto File. Esto fallará para archivos >20MB.
        telegram_file_obj = await file.get_file()

        with tempfile.NamedTemporaryFile(suffix=f"_{file.file_name}") as temp_file:
            logger.info(f"Descargando chunk para el archivo: {file.file_name}")
            await telegram_file_obj.download_to_drive(custom_path=temp_file.name, read_timeout=60, write_timeout=60)
            
            logger.info(f"Chunk descargado. Analizando con MediaInfo...")
            media_info = MediaInfo.parse(temp_file.name, output="JSON")
            data = json.loads(media_info)
            logger.info("Análisis de MediaInfo completado.")
            return data

    except BadRequest as e:
        # Capturamos el error específico de Telegram
        if "File is too big" in e.message:
            logger.warning(f"El archivo '{file.file_name}' es demasiado grande (>20MB) para MediaInfo. Se omitirán los datos técnicos.")
            return None # Devolvemos None para que el bot sepa que debe continuar sin estos datos.
        else:
            # Si es otro tipo de BadRequest, sí queremos saberlo.
            logger.error(f"Ocurrió un BadRequest inesperado al obtener el archivo: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error desconocido en get_media_info: {e}", exc_info=True)
        return None
