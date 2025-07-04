# /bot/modules/post_creator.py
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from bot.services import gemini, tmdb, mediainfo
from bot import templates

logger = logging.getLogger(__name__)

# --- Diccionario para mejorar la detección de MediaInfo ---
LANG_MAP = {
    "spa": "Español", "eng": "Inglés", "lat": "Latino", "jap": "Japonés"
}

# --- Funciones de Ayuda ---
def get_file_format(filename):
    return filename.split('.')[-1].upper() if '.' in filename else 'N/A'

def create_hashtags(genres):
    return " ".join([f"#{genre.replace(' ', '').replace('-', '')}" for genre in genres])

def format_runtime(minutes: int) -> str:
    if not minutes: return "N/A"
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m" if h > 0 else f"{m}m"

@Client.on_message(filters.document | filters.video)
async def file_handler(client: Client, message: Message):
    media = message.video or message.document
    if not getattr(media, "file_name", None): return

    status_message = await message.reply_text("⏳ Misión aceptada...", quote=True)

    try:
        # --- Fase 1: Análisis y Recopilación de Datos Base ---
        await status_message.edit_text("🕵️‍♂️ Analizando archivo...")
        
        is_season_pack = message.caption and ("temporada" in message.caption.lower() or "season" in message.caption.lower())
        
        info_task = mediainfo.get_media_info(client, message)
        
        if is_season_pack:
            details = await gemini.extract_season_details_from_caption(message.caption)
            if not details: # ... (código de error)
                await status_message.edit_text("❌ La IA no pudo procesar el caption de temporada.")
                return
            title, season = details.get("title"), details.get("season")
            tmdb_data = await tmdb.search_series(title, season, episode_number=None)
            template_to_use = templates.SEASON_TEMPLATE
        else: # Archivo individual
            details = await gemini.extract_media_details(media.file_name)
            if not details: # ... (código de error)
                await status_message.edit_text("❌ La IA no pudo procesar el nombre del archivo.")
                return

            media_type, title, year = details.get("type"), details.get("title"), details.get("year")
            if media_type == "movie":
                tmdb_data = await tmdb.search_movie(title, year)
                template_to_use = templates.MOVIE_TEMPLATE
            else: # Episodio de serie
                season, episode = details.get("season", 1), details.get("episode")
                tmdb_data = await tmdb.search_series(title, season, episode)
                template_to_use = templates.DEFAULT_TEMPLATE

        if not tmdb_data: # ... (código de error)
            await status_message.edit_text("❌ No se encontraron datos en TMDb.")
            return

        # --- Fase 2: Tareas de IA y Ensamblaje ---
        await status_message.edit_text("✍️ Generando descripción y datos técnicos...")
        overview = tmdb_data.get('overview', 'No hay descripción disponible.')
        tmdb_title = tmdb_data.get('title') or tmdb_data.get('name')
        desc_task = gemini.generate_creative_description(tmdb_title, overview)

        media_info_data, gemini_description = await asyncio.gather(info_task, desc_task)

        # --- Fase 3: Ensamblaje y Formateo Final ---
        await status_message.edit_text("🖼️ Ensamblando post final...")
        
        genres_list = [genre['name'] for genre in tmdb_data.get('genres', [])]
        
        post_data = {
            "title": tmdb_title, "year": (tmdb_data.get('release_date') or tmdb_data.get('air_date') or tmdb_data.get('first_air_date', 'N/A')).split('-')[0],
            "overview": f"<i>{overview}</i>", "genres": ", ".join(genres_list), "hashtags": create_hashtags(genres_list),
            "gemini_description": gemini_description, "runtime": format_runtime(tmdb_data.get('runtime')),
            "quality": "WEB-DL", "resolution": "N/A", "audio_tracks": "N/A", "subtitle_tracks": "N/A",
            "file_size": f"{media.file_size / (1024*1024*1024):.2f} GB" if media.file_size else "N/A",
            "format": get_file_format(media.file_name), "season": details.get("season"),
            "episodes_count": len(tmdb_data.get('episodes', [])) if is_season_pack else tmdb_data.get('episode_number', '')
        }

        # Plan de Respaldo: Mejorar datos de MediaInfo
        if media_info_data and media_info_data.get('media', {}).get('track'):
            tracks = media_info_data['media']['track']
            video_track = next((t for t in tracks if t.get('@type') == 'Video'), {})
            post_data["resolution"] = f"{video_track.get('Width', '')}x{video_track.get('Height', '')}"
            
            # Prioriza el Título de la pista, si no, traduce el código de 3 letras
            audios = [t.get('Title') or LANG_MAP.get(t.get('Language_String3')) for t in tracks if t.get('@type') == 'Audio']
            post_data["audio_tracks"] = ", ".join(filter(None, audios)) or "No detectado"
            
            subs = [t.get('Title') or LANG_MAP.get(t.get('Language_String3')) for t in tracks if t.get('@type') == 'Text']
            post_data["subtitle_tracks"] = ", ".join(filter(None, subs)) or "No detectado"

        # Ataque Principal: Gemini analiza el caption y tiene la última palabra
        if message.caption:
            lang_details = await gemini.extract_language_details_from_caption(message.caption)
            if lang_details:
                if lang_details.get("audio"):
                    post_data["audio_tracks"] = ", ".join(lang_details["audio"])
                if lang_details.get("subtitles"):
                    post_data["subtitle_tracks"] = ", ".join(lang_details["subtitles"])

        # Publicación
        final_caption = template_to_use.format(**post_data)
        poster_path = tmdb_data.get('poster_path') or tmdb_data.get('still_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

        await status_message.delete()
        if poster_url:
            await client.send_photo(message.chat.id, photo=poster_url, caption=final_caption, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(final_caption, quote=True, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Error catastrófico en file_handler: {e}", exc_info=True)
        await status_message.edit_text(f"❌ Ocurrió un error inesperado.\n`{e}`")