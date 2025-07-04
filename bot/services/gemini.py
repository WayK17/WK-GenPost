# /bot/services/gemini.py
import logging
import google.generativeai as genai
import json
# Cambiamos la importación
from bot import config

logger = logging.getLogger(__name__)

# Configura la API de Gemini
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Usamos el modelo más rápido

async def extract_media_details(filename: str) -> dict | None:
    """
    Usa Gemini para analizar un nombre de archivo y extraer detalles estructurados.
    """
    prompt = f"""
    Analiza el siguiente nombre de archivo: "{filename}"
    
    Extrae la siguiente información:
    1. "type": si es "movie" o "series".
    2. "title": el título principal.
    3. "year": el año de lanzamiento, si está presente.
    4. "season": el número de la temporada, solo si es una serie.
    5. "episode": el número del episodio, solo si es una serie.
    
    Responde únicamente con un objeto JSON válido. No incluyas explicaciones ni texto adicional.
    
    Ejemplos:
    - Para "El.Contador.2.(2025).1080p.mkv", la respuesta debe ser:
      {{"type": "movie", "title": "The Accountant 2", "year": 2025}}
    - Para "Más.De.La.Cuenta.S01E04.mkv", la respuesta debe ser:
      {{"type": "series", "title": "Más De La Cuenta", "season": 1, "episode": 4}}
    """
    
    logger.info(f"Enviando nombre de archivo a Gemini para análisis: {filename}")
    
    try:
        response = await model.generate_content_async(prompt)
        # Limpiamos la respuesta para asegurarnos de que sea solo el JSON
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        details = json.loads(cleaned_response)
        logger.info(f"Detalles extraídos por Gemini: {details}")
        return details
    except Exception as e:
        logger.error(f"Error al conectar o analizar la respuesta de Gemini: {e}")
        return None


async def extract_season_details_from_caption(caption: str) -> dict | None:
    """
    Usa Gemini para analizar el caption y extraer los detalles de una temporada completa.
    """
    prompt = f"""
    Analiza el siguiente texto de un caption: "{caption}"

    Extrae la siguiente información:
    1. "title": el título principal de la serie.
    2. "season": el número de la temporada.

    Responde únicamente con un objeto JSON válido.

    Ejemplos:
    - Para "The Boys Temporada 4 Completa", la respuesta debe ser:
      {{"title": "The Boys", "season": 4}}
    - Para "Temporada completa de Bleach, la 2", la respuesta debe ser:
      {{"title": "Bleach", "season": 2}}
    """
    logger.info(f"Enviando caption a Gemini para análisis de temporada: {caption}")
    try:
        response = await model.generate_content_async(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        details = json.loads(cleaned_response)
        logger.info(f"Detalles de temporada extraídos por Gemini: {details}")
        return details
    except Exception as e:
        logger.error(f"Error al analizar el caption de temporada con Gemini: {e}")
        return None


async def extract_language_details_from_caption(caption: str) -> dict | None:
    """
    Usa Gemini para analizar el caption y extraer detalles de audio y subtítulos.
    """
    prompt = f"""
    Analiza el siguiente texto de un caption: "{caption}"

    Extrae la siguiente información sobre el audio y los subtítulos:
    1. "audio": una lista de los idiomas del audio. Diferencia claramente entre "Latino" y "Castellano" o "Español".
    2. "subtitles": una lista de los idiomas de los subtítulos. Identifica si son "Forzados".

    Responde únicamente con un objeto JSON válido.

    Ejemplos:
    - Para "Audio latino e inglés con subs forzados", la respuesta debe ser:
      {{"audio": ["Latino", "Inglés"], "subtitles": ["Español (Forzados)"]}}
    - Para "Audio dual latino/inglés y subs completos", la respuesta debe ser:
      {{"audio": ["Latino", "Inglés"], "subtitles": ["Español", "Inglés"]}}
    """
    logger.info(f"Analizando caption con Gemini para detalles de idioma: {caption}")
    try:
        response = await model.generate_content_async(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        details = json.loads(cleaned_response)
        logger.info(f"Detalles de idioma extraídos por Gemini: {details}")
        return details
    except Exception as e:
        logger.error(f"Error al analizar caption de idioma con Gemini: {e}")
        return None


# Por ahora no necesitamos la función de descripción, la añadiremos luego.
async def generate_telegraph_analysis(title: str, media_info: dict) -> str:
    """
    Analiza los datos de MediaInfo con Gemini y genera un texto enriquecido para Telegraph.
    """
    if not media_info:
        return "<p><i>Análisis técnico no disponible (archivo muy grande o error de MediaInfo).</i></p>"

    # Simplificamos los datos para el prompt
    try:
        video_track = next((t for t in media_info['media']['track'] if t['@type'] == 'Video'), {})
        audio_tracks = [t for t in media_info['media']['track'] if t['@type'] == 'Audio']
        
        prompt = f"""
        Eres un experto en códecs y formatos de video. Analiza los siguientes datos técnicos para "{title}" y escribe un resumen amigable en formato HTML.

        Datos:
        - Video: Resolución {video_track.get('Width')}x{video_track.get('Height')}, Formato {video_track.get('Format')}
        - Audios: Hay {len(audio_tracks)} pistas de audio. Sus idiomas o títulos son: {[t.get('Title') or t.get('Language_String3') for t in audio_tracks]}

        En tu resumen:
        1. Comenta brevemente la calidad del video.
        2. Describe los audios disponibles de forma clara.
        3. Usa párrafos `<p>` y listas `<ul><li>...</li></ul>` para estructurar la información.
        """
        
        logger.info(f"Generando análisis técnico de Telegraph para: {title}")
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generando el análisis para Telegraph: {e}")
        return "<p>No se pudo generar el análisis técnico.</p>"

        