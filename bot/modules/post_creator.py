# /bot/modules/post_creator.py
import logging
import asyncio
from typing import Dict, Any, Optional
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from bot.services import gemini, tmdb, mediainfo, telegraph
from bot import templates

logger = logging.getLogger(__name__)

# --- Constantes y Configuración CORREGIDAS ---
LANG_MAP = {
    # Mapeo de idiomas completos a abreviaciones
    "español": "esp", "spanish": "esp", "spa": "esp",
    "ingles": "eng", "inglés": "eng", "english": "eng", "eng": "eng",
    "latino": "lat", "latin": "lat", "lat": "lat",
    "japones": "jap", "japonés": "jap", "japanese": "jap", "jap": "jap",
    "frances": "fra", "francés": "fra", "french": "fra", "fra": "fra",
    "aleman": "ger", "alemán": "ger", "german": "ger", "ger": "ger",
    "italiano": "ita", "italian": "ita", "ita": "ita",
    "portugues": "por", "português": "por", "portuguese": "por", "por": "por"
}

TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
TELEGRAPH_FALLBACK_URL = "https://telegra.ph/"

# --- Funciones de Utilidad ---
def get_file_format(filename: str) -> str:
    return filename.split('.')[-1].upper() if '.' in filename else 'N/A'

def create_hashtags(media_type: str, genres: list, ai_genres: list = None) -> str:
    """
    FUNCIÓN MEJORADA: Combina géneros de TMDb y IA para crear hashtags completos
    """
    type_hashtag = f"#{media_type.replace(' ', '')}"
    
    # Combinamos géneros de TMDb con géneros de IA
    all_genres = []
    
    # Primero los géneros de TMDb (más precisos)
    if genres:
        all_genres.extend(genres)
    
    # Luego los géneros de IA como backup/complemento
    if ai_genres and not genres:  # Solo si TMDb no tiene géneros
        all_genres.extend(ai_genres)
    
    if not all_genres:
        return type_hashtag
    
    # Limpiamos y creamos hashtags de géneros
    genre_hashtags = []
    for genre in all_genres[:3]:  # Máximo 4 géneros
        if genre and isinstance(genre, str):
            clean_genre = genre.replace(' ', '').replace('-', '').replace('&', '').replace('/', '')
            if clean_genre and len(clean_genre) > 2:  # Solo géneros válidos
                genre_hashtags.append(f"#{clean_genre}")
    
    return " ".join([type_hashtag] + genre_hashtags)

def format_runtime(minutes: Optional[int]) -> str:
    if not minutes: 
        return "N/A"
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m" if h > 0 else f"{m}m"

def format_file_size(size_bytes: Optional[int]) -> str:
    if not size_bytes: 
        return "N/A"
    return f"{size_bytes / (1024*1024*1024):.2f} GB"

def normalize_language(lang_input: str) -> str:
    """Normaliza cualquier entrada de idioma a abreviación"""
    if not lang_input or not isinstance(lang_input, str):
        return ""
    
    clean_lang = lang_input.lower().strip()
    return LANG_MAP.get(clean_lang, clean_lang)

def extract_media_tracks(media_info_data: Dict[str, Any]) -> tuple:
    """Extrae solo idiomas, no títulos contaminados"""
    base_audios, base_subs = set(), set()
    resolution = "N/A"
    
    if not media_info_data or not media_info_data.get('media', {}).get('track'):
        return base_audios, base_subs, resolution
    
    tracks = media_info_data['media']['track']
    
    # Extraer resolución
    video_track = next((t for t in tracks if t.get('@type') == 'Video'), {})
    if video_track:
        width = video_track.get('Width', '')
        height = video_track.get('Height', '')
        if width and height:
            resolution = f"{width}x{height}"
    
    # Extraer pistas de audio
    for track in tracks:
        if track.get('@type') == 'Audio':
            lang_candidate = (track.get('Language_String3') or 
                             track.get('Language') or 
                             track.get('Language_String2'))
            
            if lang_candidate:
                normalized_lang = normalize_language(lang_candidate)
                if normalized_lang and len(normalized_lang) <= 4:
                    base_audios.add(normalized_lang)
    
    # Extraer pistas de subtítulos
    for track in tracks:
        if track.get('@type') == 'Text':
            lang_candidate = (track.get('Language_String3') or 
                             track.get('Language') or 
                             track.get('Language_String2'))
            
            if lang_candidate:
                normalized_lang = normalize_language(lang_candidate)
                if normalized_lang and len(normalized_lang) <= 4:
                    base_subs.add(normalized_lang)
    
    return base_audios, base_subs, resolution

def merge_language_tracks(base_tracks: set, ai_tracks: list) -> str:
    """Combina y normaliza todas las pistas"""
    normalized_ai_tracks = [normalize_language(track) for track in ai_tracks if track]
    all_tracks = base_tracks.union(set(normalized_ai_tracks))
    filtered_tracks = [track for track in all_tracks if track and len(track) <= 4]
    
    return ", ".join(sorted(filtered_tracks)) if filtered_tracks else "N/D"

# --- Función Principal de Procesamiento ---
async def process_single_ai_request(filename: str, caption: Optional[str], media_info_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Realiza UNA SOLA llamada a Gemini para obtener todos los datos necesarios.
    """
    return await gemini.get_comprehensive_analysis(filename, caption, media_info_data)

# --- Manejador Principal Optimizado ---
@Client.on_message(filters.document | filters.video)
async def file_handler(client: Client, message: Message):
    """
    Manejador principal MEJORADO con géneros de IA e iconos dinámicos.
    """
    media = message.video or message.document
    if not getattr(media, "file_name", None): 
        return

    status_message = await message.reply_text("⏳ Misión aceptada. Protocolos iniciados...", quote=True)

    try:
        # --- Fase 1: Recolección de Datos Técnicos ---
        await status_message.edit_text("⚙️ Obteniendo datos técnicos del archivo...")
        
        media_info_task = asyncio.create_task(mediainfo.get_media_info(client, message))
        
        is_season_pack = (message.caption and 
                         ("temporada" in message.caption.lower() or "season" in message.caption.lower()))
        
        media_info_data = await media_info_task
        
        # --- Fase 2: UNA SOLA LLAMADA A LA IA MEJORADA ---
        await status_message.edit_text("🤖 Consultando a la IA (análisis completo con géneros)...")
        
        ai_comprehensive_data = await process_single_ai_request(
            media.file_name, 
            message.caption, 
            media_info_data
        )
        
        if not ai_comprehensive_data or not ai_comprehensive_data.get("details"):
            await status_message.edit_text("❌ La IA no pudo procesar la información del archivo.")
            return
        
        # Extraer TODOS los datos de la respuesta única
        details = ai_comprehensive_data.get("details", {})
        lang_details_from_ai = ai_comprehensive_data.get("language_details", {})
        content_analysis = ai_comprehensive_data.get("content_analysis", {})  # NUEVO
        gemini_analysis = ai_comprehensive_data.get("telegraph_analysis", "<p>Análisis no disponible.</p>")
        
        # --- Fase 3: Búsqueda en TMDb MEJORADA ---
        await status_message.edit_text("🎬 Buscando en la base de datos cinematográfica...")
        
        media_type = details.get("type")
        title = details.get("title")
        year = details.get("year")
        
        # Determinar tipo de búsqueda y template
        if is_season_pack:
            season = details.get("season")
            tmdb_data = await tmdb.search_series(title, season, episode_number=None)
            template_to_use = templates.SEASON_TEMPLATE
            media_type_for_hashtag = "Serie"
        elif media_type == "movie":
            tmdb_data = await tmdb.search_movie(title, year)
            template_to_use = templates.MOVIE_TEMPLATE
            media_type_for_hashtag = "Película"
        else:
            season = details.get("season", 1)
            episode = details.get("episode")
            tmdb_data = await tmdb.search_series(title, season, episode_number=episode)
            template_to_use = templates.DEFAULT_TEMPLATE
            media_type_for_hashtag = "Serie"
        
        if not tmdb_data:
            await status_message.edit_text(f"❌ No encontré '{title}' en la base de datos.")
            return
        
        # --- Fase 4: Creación del Informe Telegraph ---
        await status_message.edit_text("📄 Creando informe detallado...")
        
        overview = tmdb_data.get('overview', 'Sinopsis no disponible.')
        tmdb_title = tmdb_data.get('title') or tmdb_data.get('name')
        
        telegraph_content = (
            f"<h3>Sinopsis Oficial</h3><p><em>{overview}</em></p><hr>"
            f"<h3>Análisis del Experto (IA)</h3>{gemini_analysis}"
        )
        
        synopsis_url = await asyncio.to_thread(
            telegraph.create_page, 
            f"Detalles de {tmdb_title}", 
            telegraph_content
        )
        
        # --- Fase 5: Ensamblaje de Datos Técnicos ---
        await status_message.edit_text("🔧 Ensamblando información técnica...")
        
        base_audios, base_subs, resolution = extract_media_tracks(media_info_data)
        final_audios = merge_language_tracks(base_audios, lang_details_from_ai.get("audio", []))
        final_subs = merge_language_tracks(base_subs, lang_details_from_ai.get("subtitles", []))
        
        # --- Fase 6: Preparación MEJORADA con géneros e iconos ---
        tmdb_genres_list = [genre['name'] for genre in tmdb_data.get('genres', [])]
        ai_genres_list = content_analysis.get("probable_genres", [])
        content_type = content_analysis.get("content_type", "live_action")
        
        release_date = (tmdb_data.get('release_date') or 
                       tmdb_data.get('air_date') or 
                       tmdb_data.get('first_air_date', 'N/A'))
        
        post_data = {
            "title": tmdb_title,
            "year": release_date.split('-')[0] if release_date != 'N/A' else 'N/A',
            "hashtags": create_hashtags(media_type_for_hashtag, tmdb_genres_list, ai_genres_list),
            "synopsis_url": synopsis_url or TELEGRAPH_FALLBACK_URL,
            "runtime": format_runtime(tmdb_data.get('runtime')),
            "quality": "WEB-DL",
            "file_size": format_file_size(media.file_size),
            "format": get_file_format(media.file_name),
            "season": details.get("season"),
            "episode": details.get("episode"),
            "episodes_count": (len(tmdb_data.get('episodes', [])) if is_season_pack 
                             else tmdb_data.get('episode_number')),
            "resolution": resolution,
            "audio_tracks": final_audios,  # CORREGIDO
            "subtitle_tracks": final_subs,  # CORREGIDO
            "series_title": title,
            "episode_title": tmdb_title if media_type == 'series' else ''
        }
        
        # --- Fase 7: Publicación Final ---
        await status_message.edit_text("🚀 Publicando contenido...")
        
        final_caption = template_to_use.format(**post_data)
        poster_path = tmdb_data.get('poster_path') or tmdb_data.get('still_path')
        poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None
        
        await status_message.delete()
        
        if poster_url:
            await client.send_photo(
                message.chat.id, 
                photo=poster_url, 
                caption=final_caption, 
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply_text(
                final_caption, 
                quote=True, 
                parse_mode=ParseMode.HTML
            )
    
    except Exception as e:
        logger.error(f"Error catastrófico en file_handler: {e}", exc_info=True)
        await status_message.edit_text(f"❌ Ocurrió un error inesperado.\n`{e}`")