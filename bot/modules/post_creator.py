# /bot/modules/post_creator.py
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from bot.services import gemini, tmdb, mediainfo, telegraph
from bot import templates

logger = logging.getLogger(__name__)

# --- Constantes y Configuración ---
LANG_MAP = {
    "spa": "Español", 
    "eng": "Inglés", 
    "lat": "Latino", 
    "jap": "Japonés"
}

TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
TELEGRAPH_FALLBACK_URL = "https://telegra.ph/"

# --- Funciones de Utilidad ---
def get_file_format(filename: str) -> str:
    """Extrae el formato del archivo desde el nombre."""
    return filename.split('.')[-1].upper() if '.' in filename else 'N/A'

def create_hashtags(media_type: str, genres: List[str]) -> str:
    """Crea hashtags basados en el tipo de media y géneros."""
    type_hashtag = f"#{media_type.replace(' ', '')}"
    genre_hashtags = [f"#{genre.replace(' ', '').replace('-', '')}" for genre in genres]
    return " ".join([type_hashtag] + genre_hashtags)

def format_runtime(minutes: Optional[int]) -> str:
    """Formatea la duración en minutos a formato legible."""
    if not minutes:
        return "N/A"
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m" if h > 0 else f"{m}m"

def format_file_size(size_bytes: Optional[int]) -> str:
    """Formatea el tamaño del archivo a GB."""
    if not size_bytes:
        return "N/A"
    return f"{size_bytes / (1024*1024*1024):.2f} GB"

def extract_year_from_date(date_str: str) -> str:
    """Extrae el año de una fecha en formato ISO."""
    return date_str.split('-')[0] if date_str else "N/A"

# --- Funciones de Procesamiento de Datos ---
def extract_media_info_tracks(media_info_data: Dict[str, Any]) -> Tuple[str, set, set]:
    """Extrae información de pistas de audio y subtítulos del MediaInfo."""
    resolution = "N/A"
    base_audios = set()
    base_subs = set()
    
    if not media_info_data or not media_info_data.get('media', {}).get('track'):
        return resolution, base_audios, base_subs
    
    tracks = media_info_data['media']['track']
    
    # Extraer resolución del video
    video_track = next((t for t in tracks if t.get('@type') == 'Video'), {})
    if video_track:
        width = video_track.get('Width', '')
        height = video_track.get('Height', '')
        if width and height:
            resolution = f"{width}x{height}"
    
    # Extraer pistas de audio
    audio_tracks = [t for t in tracks if t.get('@type') == 'Audio']
    for track in audio_tracks:
        title = track.get('Title') or LANG_MAP.get(track.get('Language_String3'))
        if title:
            base_audios.add(title)
    
    # Extraer pistas de subtítulos
    subtitle_tracks = [t for t in tracks if t.get('@type') == 'Text']
    for track in subtitle_tracks:
        title = track.get('Title') or LANG_MAP.get(track.get('Language_String3'))
        if title:
            base_subs.add(title)
    
    return resolution, base_audios, base_subs

async def process_language_details_from_caption(caption: str, base_audios: set, base_subs: set) -> Tuple[set, set]:
    """Procesa detalles de idioma desde el caption y los combina con los existentes."""
    lang_details = await gemini.extract_language_details_from_caption(caption)
    
    if lang_details:
        base_audios.update(lang_details.get("audio", []))
        base_subs.update(lang_details.get("subtitles", []))
    
    return base_audios, base_subs

def format_language_tracks(tracks: set) -> str:
    """Formatea las pistas de idioma para mostrar."""
    filtered_tracks = list(filter(None, tracks))
    return ", ".join(sorted(filtered_tracks)) if filtered_tracks else "No detectado"

# --- Funciones de Construcción de Datos ---
def build_base_post_data(tmdb_data: Dict[str, Any], media: Any, details: Dict[str, Any]) -> Dict[str, Any]:
    """Construye los datos base del post."""
    tmdb_title = tmdb_data.get('title') or tmdb_data.get('name')
    release_date = (tmdb_data.get('release_date') or 
                   tmdb_data.get('air_date') or 
                   tmdb_data.get('first_air_date', 'N/A'))
    
    return {
        "title": tmdb_title,
        "year": extract_year_from_date(release_date),
        "runtime": format_runtime(tmdb_data.get('runtime')),
        "quality": "WEB-DL",
        "file_size": format_file_size(media.file_size),
        "format": get_file_format(media.file_name),
        "season": details.get("season"),
        "episode": details.get("episode"),
        "resolution": "N/A",
        "audio_tracks": "N/A",
        "subtitle_tracks": "N/A"
    }

def build_hashtags_for_post(media_type_for_hashtag: str, tmdb_data: Dict[str, Any]) -> str:
    """Construye los hashtags para el post."""
    genres_list = [genre['name'] for genre in tmdb_data.get('genres', [])]
    return create_hashtags(media_type_for_hashtag, genres_list)

async def create_telegraph_page(tmdb_title: str, tmdb_data: Dict[str, Any], media_info_data: Dict[str, Any]) -> str:
    """Crea la página de Telegraph con el análisis."""
    overview = tmdb_data.get('overview', 'Sinopsis no disponible.')
    
    gemini_analysis = await gemini.generate_telegraph_analysis(tmdb_title, media_info_data)
    
    telegraph_content = f"<h3>Sinopsis Oficial</h3><p><em>{overview}</em></p><hr>"
    telegraph_content += f"<h3>Análisis del Experto (IA)</h3>{gemini_analysis}"
    
    synopsis_url = await asyncio.to_thread(
        telegraph.create_page, 
        title=f"Detalles de {tmdb_title}", 
        content=telegraph_content
    )
    
    return synopsis_url if synopsis_url else TELEGRAPH_FALLBACK_URL

# --- Funciones de Procesamiento Principal ---
async def process_season_pack(message: Message) -> Tuple[Dict[str, Any], Dict[str, Any], str, str]:
    """Procesa un paquete de temporada."""
    details = await gemini.extract_season_details_from_caption(message.caption)
    if not details:
        raise ValueError("La IA no pudo procesar el caption de temporada.")
    
    title, season = details.get("title"), details.get("season")
    tmdb_data = await tmdb.search_series(title, season, episode_number=None)
    
    if not tmdb_data:
        raise ValueError("No se encontraron datos en TMDb.")
    
    return details, tmdb_data, templates.SEASON_TEMPLATE, "Serie"

async def process_individual_file(media: Any) -> Tuple[Dict[str, Any], Dict[str, Any], str, str]:
    """Procesa un archivo individual (película o episodio)."""
    details = await gemini.extract_media_details(media.file_name)
    if not details:
        raise ValueError("La IA no pudo procesar el nombre del archivo.")
    
    media_type = details.get("type")
    title = details.get("title")
    year = details.get("year")
    
    if media_type == "movie":
        media_type_for_hashtag = "Película"
        tmdb_data = await tmdb.search_movie(title, year)
        template_to_use = templates.MOVIE_TEMPLATE
    else:  # Episodio de serie
        media_type_for_hashtag = "Serie"
        season = details.get("season", 1)
        episode = details.get("episode")
        tmdb_data = await tmdb.search_series(title, season, episode)
        template_to_use = templates.DEFAULT_TEMPLATE
    
    if not tmdb_data:
        raise ValueError("No se encontraron datos en TMDb.")
    
    return details, tmdb_data, template_to_use, media_type_for_hashtag

async def enhance_post_data_with_media_info(post_data: Dict[str, Any], media_info_data: Dict[str, Any], 
                                          message: Message, tmdb_data: Dict[str, Any], 
                                          is_season_pack: bool) -> Dict[str, Any]:
    """Mejora los datos del post con información de MediaInfo."""
    # Extraer información técnica
    resolution, base_audios, base_subs = extract_media_info_tracks(media_info_data)
    post_data["resolution"] = resolution
    
    # Procesar idiomas desde el caption si existe
    if message.caption:
        base_audios, base_subs = await process_language_details_from_caption(
            message.caption, base_audios, base_subs
        )
    
    # Formatear pistas de idioma
    post_data["audio_tracks"] = format_language_tracks(base_audios)
    post_data["subtitle_tracks"] = format_language_tracks(base_subs)
    
    # Agregar conteo de episodios
    if is_season_pack:
        post_data["episodes_count"] = len(tmdb_data.get('episodes', []))
    else:
        post_data["episodes_count"] = tmdb_data.get('episode_number')
    
    return post_data

async def send_final_post(client: Client, message: Message, tmdb_data: Dict[str, Any], 
                         final_caption: str) -> None:
    """Envía el post final con la imagen del poster."""
    poster_path = tmdb_data.get('poster_path') or tmdb_data.get('still_path')
    poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None
    
    await client.send_photo(
        message.chat.id, 
        photo=poster_url, 
        caption=final_caption, 
        parse_mode=ParseMode.HTML
    )

# --- Manejador Principal ---
@Client.on_message(filters.document | filters.video)
async def file_handler(client: Client, message: Message):
    """Manejador principal para procesar archivos de video y documentos."""
    # Validación inicial
    media = message.video or message.document
    if not getattr(media, "file_name", None):
        return

    status_message = await message.reply_text("⏳ Misión aceptada. Protocolos iniciados...", quote=True)

    try:
        # --- Fase 1: Iniciar Tareas en Paralelo y Análisis Inicial ---
        await status_message.edit_text("🕵️‍♂️ Analizando archivo y iniciando tareas de fondo...")
        
        # Optimización: Iniciar MediaInfo en segundo plano
        info_task = asyncio.create_task(mediainfo.get_media_info(client, message))
        
        # Determinar tipo de contenido y procesar
        is_season_pack = (message.caption and 
                         ("temporada" in message.caption.lower() or "season" in message.caption.lower()))
        
        if is_season_pack:
            details, tmdb_data, template_to_use, media_type_for_hashtag = await process_season_pack(message)
        else:
            details, tmdb_data, template_to_use, media_type_for_hashtag = await process_individual_file(media)

        # --- Fase 2: Creación del Informe Detallado para Telegraph ---
        await status_message.edit_text("📄 Esperando datos técnicos para crear el informe...")
        
        # Esperar a que MediaInfo termine
        media_info_data = await info_task
        
        await status_message.edit_text("✍️ Generando análisis para Telegraph...")
        
        # Crear página de Telegraph
        tmdb_title = tmdb_data.get('title') or tmdb_data.get('name')
        synopsis_url = await create_telegraph_page(tmdb_title, tmdb_data, media_info_data)

        # --- Fase 3: Ensamblaje y Publicación ---
        await status_message.edit_text("🖼️ Ensamblando post final...")
        
        # Construir datos base del post
        post_data = build_base_post_data(tmdb_data, media, details)
        post_data["hashtags"] = build_hashtags_for_post(media_type_for_hashtag, tmdb_data)
        post_data["synopsis_url"] = synopsis_url
        
        # Mejorar datos con información de MediaInfo
        post_data = await enhance_post_data_with_media_info(
            post_data, media_info_data, message, tmdb_data, is_season_pack
        )
        
        # Generar caption final y enviar
        final_caption = template_to_use.format(**post_data)
        
        await status_message.delete()
        await send_final_post(client, message, tmdb_data, final_caption)

    except ValueError as ve:
        logger.warning(f"Error de validación en file_handler: {ve}")
        await status_message.edit_text(f"❌ {ve}")
    except Exception as e:
        logger.error(f"Error catastrófico en file_handler: {e}", exc_info=True)
        await status_message.edit_text(f"❌ Ocurrió un error inesperado.\n`{e}`")