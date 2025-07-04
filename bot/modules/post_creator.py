# /bot/modules/post_creator.py
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from bot.services import gemini, tmdb, mediainfo
from bot import templates

logger = logging.getLogger(__name__)

# --- Funciones de Ayuda para Formateo ---

def get_file_format(filename):
    """Extrae la extensión del archivo para usarla como formato."""
    return filename.split('.')[-1].upper() if '.' in filename else 'N/A'

def create_hashtags(genres):
    """Crea hashtags a partir de una lista de géneros."""
    return " ".join([f"#{genre.replace(' ', '').replace('-', '')}" for genre in genres])

def format_runtime(minutes: int) -> str:
    """Convierte minutos a un formato de '1h 45m'."""
    if not minutes:
        return "N/A"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

# --- Manejador Principal ---

@Client.on_message(filters.document | filters.video)
async def file_handler(client: Client, message: Message):
    media = message.video or message.document
    if not getattr(media, "file_name", None):
        return

    status_message = await message.reply_text("⏳ Misión aceptada. Iniciando análisis...", quote=True)

    try:
        # Lógica para detectar si es un pack de temporada por el caption
        is_season_pack = message.caption and ("temporada" in message.caption.lower() or "season" in message.caption.lower())

        info_task = mediainfo.get_media_info(client, message)
        
        if is_season_pack:
            # --- FLUJO PARA TEMPORADA COMPLETA ---
            await status_message.edit_text("📦 Detectado pack de temporada. Analizando...")
            details = await gemini.extract_season_details_from_caption(message.caption)
            if not details: #... (código de error)
                await status_message.edit_text("❌ La IA no pudo procesar el caption.")
                return
            
            title, season = details.get("title"), details.get("season")
            tmdb_data = await tmdb.search_series(title, season, episode_number=None)
            template_to_use = templates.SEASON_TEMPLATE

        else:
            # --- FLUJO PARA ARCHIVO INDIVIDUAL ---
            await status_message.edit_text("🕵️‍♂️ Analizando nombre de archivo con IA...")
            details = await gemini.extract_media_details(media.file_name)
            if not details: #... (código de error)
                await status_message.edit_text("❌ La IA no pudo procesar el nombre del archivo.")
                return

            media_type = details.get("type")
            title = details.get("title")
            year = details.get("year")
            
            if media_type == "movie":
                tmdb_data = await tmdb.search_movie(title, year)
                template_to_use = templates.MOVIE_TEMPLATE # Usamos la nueva plantilla de película
            else: # series
                season = details.get("season", 1)
                episode = details.get("episode")
                tmdb_data = await tmdb.search_series(title, season, episode)
                template_to_use = templates.DEFAULT_TEMPLATE # Usamos la plantilla por defecto para episodios

        if not tmdb_data: #... (código de error)
            await status_message.edit_text("❌ No se encontraron datos en TMDb.")
            return

        # --- RECOLECCIÓN FINAL Y ENSAMBLAJE ---
        await status_message.edit_text("✍️ Generando descripción y recolectando datos técnicos...")
        overview = tmdb_data.get('overview', 'No hay descripción disponible.')
        tmdb_title = tmdb_data.get('title') or tmdb_data.get('name')
        desc_task = gemini.generate_creative_description(tmdb_title, overview)

        media_info_data, gemini_description = await asyncio.gather(info_task, desc_task)

        await status_message.edit_text("🖼️ Ensamblando post final...")
        
        # --- PREPARACIÓN DE DATOS PARA LA PLANTILLA ---
        genres_list = [genre['name'] for genre in tmdb_data.get('genres', [])]
        
        post_data = {
            "title": tmdb_title,
            "year": (tmdb_data.get('release_date') or tmdb_data.get('air_date') or tmdb_data.get('first_air_date', 'N/A')).split('-')[0],
            "overview": f"<i>{overview}</i>",
            "genres": ", ".join(genres_list),
            "hashtags": create_hashtags(genres_list),
            "gemini_description": gemini_description,
            "runtime": format_runtime(tmdb_data.get('runtime')),
            "quality": "WEB-DL", # Esto se puede mejorar después para que sea dinámico
            "resolution": "N/A", "audio_tracks": "N/A", "subtitle_tracks": "N/A",
            "file_size": f"{media.file_size / (1024*1024*1024):.2f} GB" if media.file_size else "N/A", # Formateado a GB
            "format": get_file_format(media.file_name),
            "season": season if not is_season_pack and media_type == 'series' else (season if is_season_pack else None),
            "episodes_count": len(tmdb_data.get('episodes', [])) if is_season_pack else (tmdb_data.get('episode_number', 'N/A'))
        }

        # Lógica para poblar datos de MediaInfo
        if media_info_data and media_info_data.get('media', {}).get('track'):
            tracks = media_info_data['media']['track']
            video_track = next((t for t in tracks if t.get('@type') == 'Video'), {})
            post_data["resolution"] = f"{video_track.get('Width', '')}x{video_track.get('Height', '')}"
            audios = [t.get('Language_String3', t.get('Title')) for t in tracks if t.get('@type') == 'Audio']
            post_data["audio_tracks"] = ", ".join(filter(None, audios)) or "No detectado"
            subs = [t.get('Language_String3', t.get('Title')) for t in tracks if t.get('@type') == 'Text']
            post_data["subtitle_tracks"] = ", ".join(filter(None, subs)) or "No detectado"

        final_caption = template_to_use.format(**post_data)
        poster_path = tmdb_data.get('poster_path') or tmdb_data.get('still_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

        # --- PUBLICACIÓN ---
        await status_message.delete()
        if poster_url:
            await client.send_photo(message.chat.id, photo=poster_url, caption=final_caption, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(final_caption, quote=True, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Error catastrófico en file_handler: {e}", exc_info=True)
        await status_message.edit_text(f"❌ Ocurrió un error inesperado.\n`{e}`")