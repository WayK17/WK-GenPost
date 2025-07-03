# /bot/handlers.py
import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# Cambiamos las importaciones
from bot.services import gemini, tmdb, mediainfo
from bot import templates

logger = logging.getLogger(__name__)

async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Manejador final que orquesta todo el proceso de creación del post.
    """
    video_file = update.message.video or update.message.document
    if not video_file:
        return

    status_message = await update.message.reply_text("⏳ Iniciando proceso... Misión aceptada.")

    try:
        # --- PASO 1: EXTRAER INFO DEL NOMBRE (GEMINI) ---
        await status_message.edit_text("🕵️‍♂️ Analizando nombre del archivo con IA...")
        media_details = await gemini.extract_media_details(video_file.file_name)
        if not media_details:
            await status_message.edit_text("❌ La IA no pudo procesar el nombre del archivo.")
            return

        # --- PASO 2: OBTENER DATOS DE TMDB ---
        media_type = media_details.get("type")
        title = media_details.get("title")
        year = media_details.get("year")
        
        if media_type == "movie":
            await status_message.edit_text(f"🎬 Buscando película: {title} ({year})...")
            tmdb_data = await tmdb.search_movie(title, year)
        elif media_type == "series":
            season = media_details.get("season", 1)
            episode = media_details.get("episode")
            await status_message.edit_text(f"📺 Buscando episodio: {title} S{season:02d}E{episode:02d}...")
            tmdb_data = await tmdb.search_series(title, season, episode)
        else:
            await status_message.edit_text("🤔 Tipo de medio no reconocido.")
            return

        if not tmdb_data:
            await status_message.edit_text("❌ No se encontraron datos en TMDb.")
            return

        # --- PASO 3: OBTENER DATOS TÉCNICOS Y DESCRIPCIÓN (EN PARALELO) ---
        await status_message.edit_text("⚙️ Extrayendo datos técnicos y generando descripción creativa...")
        
        # Ejecutamos estas dos tareas al mismo tiempo para máxima eficiencia
        info_task = asyncio.create_task(mediainfo.get_media_info(video_file))
        desc_task = asyncio.create_task(
            gemini.generate_creative_description(
                tmdb_data.get('title') or tmdb_data.get('name'), 
                tmdb_data.get('overview', '')
            )
        )
        
        media_info_data, gemini_description = await asyncio.gather(info_task, desc_task)

        # --- PASO 4: ENSAMBLAR EL POST ---
        await status_message.edit_text("✍️ Ensamblando el post final...")

        # Procesamos los datos para la plantilla
        post_data = {
            "title": tmdb_data.get('title') or tmdb_data.get('name', 'N/A'),
            "year": (tmdb_data.get('release_date') or tmdb_data.get('air_date', 'N/A')).split('-')[0],
            "overview": tmdb_data.get('overview', 'Sin sinopsis.'),
            "genres": ", ".join([genre['name'] for genre in tmdb_data.get('genres', [])]),
            "gemini_description": gemini_description,
            "resolution": "N/A",
            "audio_tracks": "N/A",
            "subtitle_tracks": "N/A",
            "file_size": f"{video_file.file_size / (1024*1024):.2f} MB"
        }

        # Extraemos y formateamos datos de MediaInfo si existen
        if media_info_data and media_info_data.get('media', {}).get('track'):
            tracks = media_info_data['media']['track']
            video_track = next((t for t in tracks if t.get('@type') == 'Video'), {})
            audio_tracks = [t for t in tracks if t.get('@type') == 'Audio']
            subtitle_tracks = [t for t in tracks if t.get('@type') == 'Text']
            
            post_data["resolution"] = f"{video_track.get('Width', '')}x{video_track.get('Height', '')}"
            post_data["audio_tracks"] = ", ".join([t.get('Language_String3', t.get('Title', '')) for t in audio_tracks])
            post_data["subtitle_tracks"] = ", ".join([t.get('Language_String3', t.get('Title', '')) for t in subtitle_tracks])

        # Formateamos la plantilla final
        final_caption = templates.DEFAULT_TEMPLATE.format(**post_data)
        poster_path = tmdb_data.get('poster_path') or tmdb_data.get('still_path')
        poster_url = f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else None

        # --- PASO 5: ENVIAR EL RESULTADO ---
        await status_message.delete() # Borramos el mensaje de estado

        if poster_url:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=poster_url,
                caption=final_caption,
                parse_mode=ParseMode.HTML # O ParseMode.MARKDOWN_V2 si prefieres
            )
        else: # Si no hay póster, enviamos solo texto
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=final_caption,
                parse_mode=ParseMode.HTML
            )

    except Exception as e:
        logger.error(f"Error catastrófico en el file_handler: {e}", exc_info=True)
        await status_message.edit_text(f"❌ Ocurrió un error inesperado durante el proceso.\nError: {e}")