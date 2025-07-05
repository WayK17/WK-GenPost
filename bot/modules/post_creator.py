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

QUALITY_TAGS = {
    "WEB-DL": ["web-dl", "webdl"],
    "WEBRip": ["web-rip", "webrip"],
    "BDRip": ["bdrip", "bluray", "bd-rip"],
    "HDRip": ["hdrip"],
    "HDTV": ["hdtv"],
    "DVDRip": ["dvdrip"],
    "CAM": ["cam", "camrip"],
    "TS": ["ts", "telesync"]
}

TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
TELEGRAPH_FALLBACK_URL = "https://telegra.ph/"

# --- Funciones de Utilidad ---
def get_file_format(filename: str) -> str:
    return filename.split('.')[-1].upper() if '.' in filename else 'N/A'

def parse_quality(text: str) -> Optional[str]:
    """
    NUEVA FUNCIÓN: Analiza un texto (filename o caption) para encontrar
    una etiqueta de calidad conocida.
    """
    if not text:
        return None
    # Preparamos el texto para una búsqueda más fácil (minúsculas, sin puntos)
    lower_text = text.lower().replace('.', ' ').replace('-', ' ')
    for quality, tags in QUALITY_TAGS.items():
        for tag in tags:
            if tag in lower_text:
                return quality
    return None # No se encontró ninguna etiqueta conocida


def create_hashtags(media_type: str, genres: list, ai_genres: list = None) -> str:
    """
    FUNCIÓN MEJORADA: Crea hashtags en dos líneas separadas para mayor elegancia.
    Línea 1: #Película o #Serie
    Línea 2: #Genero1 #Genero2 #Genero3
    """
    type_hashtag = f"#{media_type.replace(' ', '')}"
    
    # Combinamos géneros de TMDb con géneros de IA (backup)
    all_genres = []
    if genres:
        all_genres.extend(genres)
    elif ai_genres:
        all_genres.extend(ai_genres)
        
    if not all_genres:
        return type_hashtag

    # Limpiamos y creamos hashtags de géneros (máximo 3)
    genre_hashtags = []
    for genre in all_genres[:3]: # Tomamos solo los primeros 3 géneros
        if genre and isinstance(genre, str):
            clean_genre = genre.replace(' ', '').replace('-', '').replace('&', '').replace('/', '')
            if clean_genre and len(clean_genre) > 2:
                genre_hashtags.append(f"#{clean_genre}")
    
    # Devolvemos el string con un salto de línea
    return f"{type_hashtag}\n{' '.join(genre_hashtags)}"

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
async def process_single_ai_request(filename: str, caption: Optional[str], media_info_data: Dict[str, Any], tmdb_data_for_formatting: Dict[str, Any]) -> Dict[str, Any]:
    """
    Realiza UNA SOLA llamada a Gemini para obtener todos los datos necesarios.
    """
    return await gemini.get_comprehensive_analysis(filename, caption, media_info_data, tmdb_data_for_formatting)

# --- Manejador Principal Optimizado ---
@Client.on_message(filters.document | filters.video)
async def file_handler(client: Client, message: Message):
    """
    Manejador principal con el flujo de datos ORIGINAL y corregido.
    """
    media = message.video or message.document
    if not getattr(media, "file_name", None):
        return

    # CRÍTICO: Almacenar el ID del mensaje original INMEDIATAMENTE
    original_message_id = message.id
    original_chat_id = message.chat.id
    
    # Debug logging
    logger.info(f"[DEBUG] Mensaje original ID: {original_message_id}")
    logger.info(f"[DEBUG] Chat ID: {original_chat_id}")
    
    status_message = await message.reply_text("⏳ Misión aceptada. Protocolos iniciados...", quote=True)
    
    # Verificar que el status_message no interfiera
    logger.info(f"[DEBUG] Status message ID: {status_message.id}")

    try:
        # --- Fase 1: Recolección de Datos Técnicos ---
        await status_message.edit_text("⚙️ Obteniendo datos técnicos del archivo...")
        media_info_data = await mediainfo.get_media_info(client, message)

        # --- Fase 2: LLAMADA ÚNICA A LA IA ---
        await status_message.edit_text("🤖 Consultando a la IA (petición única)...")
        ai_comprehensive_data = await gemini.get_comprehensive_analysis(
            media.file_name,
            message.caption,
            media_info_data
        )

        if not ai_comprehensive_data or not ai_comprehensive_data.get("details"):
            await status_message.edit_text("❌ La IA no pudo procesar la información del archivo.")
            return
        
        # Extraer detalles para la búsqueda
        details_from_ai = ai_comprehensive_data.get("details", {})
        title = details_from_ai.get("title")
        year = details_from_ai.get("year")
        media_type = details_from_ai.get("type")
        season = details_from_ai.get("season")
        episode = details_from_ai.get("episode")
        
        # --- Fase 3: Búsqueda en TMDb ---
        await status_message.edit_text(f"🎬 Buscando '{title}' en la base de datos...")
        tmdb_data = None
        if media_type == "movie":
            tmdb_data = await tmdb.search_movie(title, year)
        elif media_type == "series":
            tmdb_data = await tmdb.search_series(title, year, season, episode)

        if not tmdb_data:
            await status_message.edit_text(f"❌ No encontré '{title}' en la base de datos de TMDb.")
            return

        # --- Fase 4: Creación de Contenido y Ensamblaje ---
        await status_message.edit_text("📄 Creando informe detallado...")

        # Crear contenido para Telegraph usando los datos oficiales de TMDb
        tmdb_title = tmdb_data.get('title') or tmdb_data.get('name')
        overview = tmdb_data.get('overview', 'Sinopsis no disponible.')
        
        # Construir HTML para Telegraph con datos de TMDb
        telegraph_content_parts = [f"<h3>Sinopsis Oficial</h3><p><em>{overview}</em></p>"]
        
        # Añadir detalles del elenco y director si existen en tmdb_data
        credits = tmdb_data.get('credits', {})
        cast = credits.get('cast', [])
        crew = credits.get('crew', [])
        if cast:
            actor_list = "".join([f"<li><b>{actor['name']}</b> como {actor['character']}</li>" for actor in cast[:5]])
            telegraph_content_parts.append(f"<h3>Elenco Principal</h3><ul>{actor_list}</ul>")
        
        director = next((person['name'] for person in crew if person.get('job') == 'Director'), None)
        if director:
             telegraph_content_parts.append(f"<p><b>Director:</b> {director}</p>")

        telegraph_content = "".join(telegraph_content_parts)
        
        synopsis_url = await asyncio.to_thread(
            telegraph.create_page,
            f"Detalles de {tmdb_title}",
            telegraph_content
        )
        
        # --- Fase 5: Preparar datos finales para la plantilla ---
        # Extraer el resto de datos de la IA
        lang_details_from_ai = ai_comprehensive_data.get("language_details", {})
        content_analysis_from_ai = ai_comprehensive_data.get("content_analysis", {})
        
        # Preparar datos
        base_audios, base_subs, resolution = extract_media_tracks(media_info_data)
        media_type_for_hashtag = "Película" if media_type == "movie" else "Serie"
        
        # Usar géneros de TMDb como fuente principal, y los de la IA como respaldo
        tmdb_genres_list = [genre['name'] for genre in tmdb_data.get('genres', [])]
        ai_genres_list = content_analysis_from_ai.get("probable_genres", [])     

        # Contamos los episodios si es una temporada y nos aseguramos de tener todas las llaves.
        episodes_count = len(tmdb_data.get('episodes', [])) if media_type == 'series' else 0 

        # --- LÓGICA DE DETECCIÓN DE CALIDAD ---
        detected_quality = "N/A"
        if message.caption:
            quality_from_caption = parse_quality(message.caption)
            if quality_from_caption:
                detected_quality = quality_from_caption

        if detected_quality == "N/A": # Si no se encontró en el caption
            quality_from_filename = parse_quality(media.file_name)
            if quality_from_filename:
                detected_quality = quality_from_filename
        
        # Si después de todo no se encontró, ponemos un default
        if detected_quality == "N/A":
            detected_quality = "WEB-DL"
        
        post_data = {
            "title": tmdb_title,
            "year": (tmdb_data.get('release_date') or tmdb_data.get('first_air_date', 'N/A')).split('-')[0],
            "hashtags": create_hashtags(media_type_for_hashtag, tmdb_genres_list, ai_genres_list),
            "synopsis_url": synopsis_url or TELEGRAPH_FALLBACK_URL,
            "runtime": format_runtime(tmdb_data.get('runtime')),
            "quality": detected_quality,
            "file_size": format_file_size(media.file_size),
            "format": get_file_format(media.file_name),
            "resolution": resolution,
            "audio_tracks": merge_language_tracks(base_audios, lang_details_from_ai.get("audio", [])),
            "subtitle_tracks": merge_language_tracks(base_subs, lang_details_from_ai.get("subtitles", [])),
            
            # --- LLAVES AÑADIDAS PARA EVITAR ERRORES ---
            "series_title": title,  # Título general de la serie
            "season": season if season is not None else 0, # Default a 0 si es None
            "episode": episode if episode is not None else 0, # Default a 0 si es None
            "episode_title": tmdb_title if media_type == 'series' and episode is not None else '',
            "episodes_count": episodes_count
        }

        # --- Fase 6: Publicación Final ---
        await status_message.edit_text("🚀 Publicando contenido...")
        
        is_season_pack = (message.caption and ("temporada" in message.caption.lower() or "season" in message.caption.lower()))
        template_to_use = templates.SEASON_TEMPLATE if is_season_pack else (templates.MOVIE_TEMPLATE if media_type == "movie" else templates.DEFAULT_TEMPLATE)
        final_caption = template_to_use.format(**post_data)

        poster_path = tmdb_data.get('poster_path')
        poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None

        await status_message.delete()
        if poster_url:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=poster_url,
                caption=final_caption,
                parse_mode=ParseMode.HTML,
                reply_to_message_id=message.id  # <-- ESTA LÍNEA ES CRUCIAL
            )
        else:
            await client.send_message(
                chat_id=message.chat.id,
                text=final_caption,
                parse_mode=ParseMode.HTML,
                reply_to_message_id=message.id, # <-- Y ESTA TAMBIÉN
                disable_web_page_preview=True
            )

    except Exception as e:
        logger.error(f"Error catastrófico en file_handler: {e}", exc_info=True)
        await status_message.edit_text(f"💥 ¡Uy! Hubo un error inesperado:\n`{e}`")
    finally:
        # Limpieza de archivos temporales
        if media_info_data and "temp_file_path" in media_info_data:
            try:
                os.remove(media_info_data["temp_file_path"])
                logger.info(f"Archivo temporal eliminado: {media_info_data['temp_file_path']}")
            except OSError as e:
                logger.error(f"Error al eliminar archivo temporal: {e}")