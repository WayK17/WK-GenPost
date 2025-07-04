# /bot/services/gemini.py
import logging
import json
from .. import config
import google.generativeai as genai

logger = logging.getLogger(__name__)

genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

async def get_all_ai_details(filename: str, caption: str | None, media_info: dict | None) -> dict | None:
    """
    Función maestra que obtiene TODOS los detalles de la IA en una sola llamada.
    """
    # Preparamos un resumen de MediaInfo para el prompt
    tech_summary = "No disponible."
    if media_info and media_info.get('media', {}).get('track'):
        tracks = media_info['media']['track']
        video_track = next((t for t in tracks if t.get('@type') == 'Video'), {})
        audio_tracks = [t for t in tracks if t.get('@type') == 'Audio']
        tech_summary = (f"Video: {video_track.get('Format')} a {video_track.get('Width')}x{video_track.get('Height')}. "
                        f"Audios: {len(audio_tracks)} pistas con idiomas/títulos: {[t.get('Title') or t.get('Language_String3') for t in audio_tracks]}")

    prompt = f"""
    Analiza el siguiente archivo y su información. Responde ÚNICAMENTE con un objeto JSON.
    - Filename: "{filename}"
    - Caption: "{caption if caption else 'No hay caption.'}"
    - Resumen Técnico de MediaInfo: "{tech_summary}"

    Tu respuesta JSON debe tener esta estructura exacta:
    {{
      "details": {{
        "type": "movie" | "series",
        "title": "Título Principal",
        "year": AÑO | null,
        "season": NÚMERO | null,
        "episode": NÚMERO | null
      }},
      "language_details": {{
        "audio": ["Idioma1", "Idioma2"],
        "subtitles": ["IdiomaSub1", "IdiomaSub2 (Forzados)"]
      }},
      "telegraph_analysis": "Un análisis técnico amigable y atractivo en formato HTML sobre la calidad, basado en el resumen técnico."
    }}
    
    Instrucciones Clave:
    1. Para "details", analiza el Filename.
    2. Para "language_details", la información en el Caption tiene la MÁXIMA prioridad. Si no hay, déjalo vacío.
    3. Para "telegraph_analysis", usa el Resumen Técnico para escribir un párrafo HTML.
    """
    
    logger.info(f"Enviando petición maestra a Gemini para: {filename}")
    try:
        response = await model.generate_content_async(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned_response)
        logger.info(f"Gemini devolvió todos los detalles en una sola llamada.")
        return data
    except Exception as e:
        logger.error(f"Error en la llamada maestra a Gemini: {e}", exc_info=True)
        return None