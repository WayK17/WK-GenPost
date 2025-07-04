# /bot/services/gemini.py

import logging
import json
from .. import config
import google.generativeai as genai

logger = logging.getLogger(__name__)

genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

async def get_comprehensive_analysis(filename: str, caption: str | None, media_info: dict | None) -> dict | None:
    """
    Función maestra que obtiene TODOS los detalles de la IA en una sola llamada.
    NUEVA VERSIÓN: Con prompt mejorado para análisis de experto y datos enriquecidos.
    """
    tech_summary = "No disponible."
    if media_info and media_info.get('media', {}).get('track'):
        tracks = media_info['media']['track']
        video_track = next((t for t in tracks if t.get('@type') == 'Video'), {})
        audio_tracks = [t for t in tracks if t.get('@type') == 'Audio']
        tech_summary = (f"Video: {video_track.get('Format')} a {video_track.get('Width')}x{video_track.get('Height')}. "
                        f"Audios: {len(audio_tracks)} pistas con idiomas/títulos: {[t.get('Title') or t.get('Language_String3') for t in audio_tracks]}")

    # --- PROMPT COMPLETAMENTE REDISEÑADO ---
    prompt = f"""
    Actúa como un experto cinéfilo y crítico de medios. Analiza la información proporcionada y responde ESTRICTAMENTE con un objeto JSON.
    - Nombre del archivo: "{filename}"
    - Caption del usuario (si existe): "{caption if caption else 'No proporcionado.'}"
    - Resumen Técnico (MediaInfo): "{tech_summary}"

    Tu respuesta DEBE ser un único objeto JSON válido, sin texto antes o después.

    {{
      "details": {{
        "type": "movie" | "series",
        "title": "Título Principal Extraído",
        "year": AÑO_NUMERICO | null,
        "season": NUMERO_TEMPORADA | null,
        "episode": NUMERO_EPISODIO | null
      }},
      "language_details": {{
        "audio": ["Idioma 1", "Idioma 2"],
        "subtitles": ["Idioma Sub 1", "Idioma Sub 2"]
      }},
      "content_analysis": {{
        "probable_genres": ["Acción", "Drama", "Ciencia Ficción"],
        "content_type": "live_action" | "anime" | "documentary" | "animation"
      }},
      "telegraph_analysis": "Un análisis detallado y atractivo en formato HTML..."
    }}

    INSTRUCCIONES DETALLADAS PARA CADA CAMPO:

    1.  **details**:
        * **title**: Extrae el título principal. Sé inteligente, ignora información de calidad como "1080p", "WEB-DL", etc.
        * **year**: Extrae el año. Si no está, pon `null`.
        * **season/episode**: Analiza patrones como "S01E01" o "- 01 -". Si es una película o no hay datos, pon `null`. Para "Bleach - 076", el episodio es 76 y la temporada es `null` si no se especifica.

    2.  **language_details**:
        * Prioriza el `Caption`. Si no existe, infiere del nombre del archivo (ej. "Latino", "Cast", "Subs"). Si no hay nada, usa `[]`.

    3.  **telegraph_analysis**:
        * Este es el campo más importante. Debe ser un string HTML.
        * Estructura la respuesta usando estas secciones, en este orden:
            * `<h3>🎬 Sinopsis</h3><p>...</p>`: Escribe una sinopsis atractiva y detallada.
            * `<h3>🌍 Detalles de Producción</h3><p><b>País:</b> ...<br><b>Año de lanzamiento:</b> ...<br><b>Estudio:</b> ...</p>`: Investiga y completa estos datos.
            * `<h3>🎭 Elenco Principal</h3><p><b>Actor 1</b> como Personaje 1<br><b>Actor 2</b> como Personaje 2</p>`: Menciona a los actores más importantes.
            * `<h3>💡 Curiosidades y Comentarios</h3><p>...</p>`: Añade datos interesantes, trivia o comentarios sobre la recepción de la obra.
            * `<h3>💻 Análisis Técnico del Archivo</h3><p>...</p>`: Usa el "Resumen Técnico" para crear un párrafo amigable sobre la calidad del video y audio.
        * **IMPORTANTE**: Si no encuentras información para una sección (ej. curiosidades), omite esa sección completa (incluyendo el `<h3>`). Sé creativo y profesional.
    """
    
    logger.info(f"Enviando petición maestra (V2) a Gemini para: {filename}")
    try:
        response = await model.generate_content_async(prompt)
        cleaned_response = response.text.strip().lstrip("```json").rstrip("```").strip()
        data = json.loads(cleaned_response)
        logger.info(f"Análisis completo (V2) de Gemini recibido exitosamente.")
        return data
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        logger.error(f"Error al decodificar la respuesta V2 de Gemini: {e}", exc_info=True)
        logger.error(f"Respuesta recibida que causó el error: {response.text}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado en la llamada a Gemini (V2): {e}", exc_info=True)
        return None