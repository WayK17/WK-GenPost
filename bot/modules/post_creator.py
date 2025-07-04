# /bot/modules/post_creator.py
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode # Importamos ParseMode

# Importamos todos nuestros activos
from bot.services import gemini, tmdb, mediainfo
from bot import templates

logger = logging.getLogger(__name__)

@Client.on_message(filters.document | filters.video)
async def file_handler(client: Client, message: Message):
    """
    Manejador principal que orquesta el flujo completo con Pyrogram.
    """
    media = message.video or message.document
    # Hacemos una comprobación más segura para el nombre del archivo
    if not getattr(media, "file_name", None):
        return

    status_message = await message.reply_text("⏳ Misión aceptada. Iniciando análisis...", quote=True)

    try:
        # PASO 1, 2 y 3 (Se quedan igual)
        await status_message.edit_text("🕵️‍♂️ Analizando nombre del archivo con IA...")
        media_details = await gemini.extract_media_details(media.file_name)
        if not media_details:
            await status_message.edit_text("❌ La IA no pudo procesar el nombre del archivo.")
            return

        await status_message.edit_text("⚙️ Obteniendo datos de TMDb y MediaInfo...")
        info_task = asyncio.create_task(mediainfo.get_media_info(client, message))
        
        tmdb_task = None
        # ... (Lógica de TMDb se queda igual)
        media_type = media_details.get("type")
        title = media_details.get("title")
        year = media_details.get("year")
        
        if media_type == "movie":
            tmdb_task = asyncio.create_task(tmdb.search_movie(title, year))
        elif media_type == "series":
            season = media_details.get("season", 1)
            episode = media_details.get("episode")
            tmdb_task = asyncio.create_task(tmdb.search_series(title, season, episode))

        results = await asyncio.gather(info_task, tmdb_task)
        media_info_data, tmdb_data = results
        
        if not tmdb_data:
            await status_message.edit_text("❌ No se encontraron datos en TMDb.")
            return

        await status_message.edit_text("✍️ Generando descripción creativa...")
        overview = tmdb_data.get('overview', 'No hay descripción disponible.')
        tmdb_title = tmdb_data.get('title') or tmdb_data.get('name')
        gemini_description = await gemini.generate_creative_description(tmdb_title, overview)

        # --- PASO 4: ENSAMBLAJE DEL POST ---
        await status_message.edit_text("🖼️ Ensamblando post final...")
        
        # ... (La lógica de post_data se queda igual)
        post_data = {
            "title": f"<b>{tmdb_title}</b>", # Usamos <b> para negrita en HTML
            "year": (tmdb_data.get('release_date') or tmdb_data.get('air_date', 'N/A')).split('-')[0],
            "overview": f"<i>{overview}</i>", # Usamos <i> para cursiva
            "genres": ", ".join([genre['name'] for genre in tmdb_data.get('genres', [])]),
            "gemini_description": gemini_description,
            "resolution": "N/A", "audio_tracks": "N/A", "subtitle_tracks": "N/A",
            "file_size": f"{media.file_size / (1024*1024):.2f} MB" if media.file_size else "N/A"
        }

        if media_info_data and media_info_data.get('media', {}).get('track'):
            # ... (Lógica de MediaInfo se queda igual)
            tracks = media_info_data['media']['track']
            video_track = next((t for t in tracks if t.get('@type') == 'Video'), {})
            post_data["resolution"] = f"<code>{video_track.get('Width', '')}x{video_track.get('Height', '')}</code>"
            audios = [t.get('Language_String3', t.get('Title')) for t in tracks if t.get('@type') == 'Audio']
            post_data["audio_tracks"] = ", ".join(filter(None, audios)) or "No detectado"
            subs = [t.get('Language_String3', t.get('Title')) for t in tracks if t.get('@type') == 'Text']
            post_data["subtitle_tracks"] = ", ".join(filter(None, subs)) or "No detectado"

        final_caption = templates.DEFAULT_TEMPLATE.format(**post_data).strip()
        poster_path = tmdb_data.get('poster_path') or tmdb_data.get('still_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

        # --- PASO 5: PUBLICACIÓN ---
        await status_message.delete()

        if poster_url:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=poster_url,
                caption=final_caption,
                parse_mode=ParseMode.HTML # ¡LA LÍNEA CLAVE!
            )
        else:
            await message.reply_text(
                final_caption, 
                quote=True,
                parse_mode=ParseMode.HTML # ¡LA LÍNEA CLAVE!
            )

    except Exception as e:
        logger.error(f"Error catastrófico en file_handler: {e}", exc_info=True)
        await status_message.edit_text(f"❌ Ocurrió un error inesperado.\n`{e}`")