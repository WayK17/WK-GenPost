# /bot/services/gemini.py
import logging
import json
from .. import config
import google.generativeai as genai

logger = logging.getLogger(__name__)

genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

async def get_comprehensive_analysis(filename: str, caption: str | None, media_info_data: dict | None) -> dict | None:
    """
    FUNCIÓN ÚNICA Y CENTRAL: Obtiene todo el análisis de la IA en una sola petición.
    Analiza el nombre del archivo, el caption y los datos técnicos.
    """
    tech_summary = "No disponible."
    if media_info_data and media_info_data.get('media', {}).get('track'):
        # ... (puedes mantener tu lógica para crear el tech_summary si lo deseas)
        tracks = media_info_data['media']['track']
        video_track = next((t for t in tracks if t.get('@type') == 'Video'), {})
        tech_summary = f"Video: {video_track.get('Format')} a {video_track.get('Width')}x{video_track.get('Height')}."

    prompt = f"""
    Analiza la información del siguiente archivo y responde ESTRICTAMENTE con un objeto JSON.
    - Nombre del archivo: "{filename}"
    - Caption (si existe): "{caption if caption else 'No proporcionado.'}"
    - Resumen Técnico (MediaInfo): "{tech_summary}"

    Tu respuesta DEBE ser un único objeto JSON con la siguiente estructura. No incluyas texto antes o después del JSON.

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
        "subtitles": ["Idioma Sub 1", "Idioma Sub 2 (Forzados)"]
      }},
      "content_analysis": {{
        "probable_genres": ["Acción", "Drama", "Comedia"]
      }}
    }}

    Instrucciones Adicionales:
    1.  **details**: Analiza el nombre del archivo para extraer el título, año, temporada y episodio. Si un campo no aplica, usa `null`.
    2.  **language_details**: La información en el `Caption` tiene la MÁXIMA prioridad. Si no hay `Caption`, infiere los idiomas del nombre del archivo. Si no es posible, déjalo como un array vacío `[]`.
    3.  **content_analysis**: Basándote en el título y el `Caption`, determina los géneros más probables.
    """
    
    logger.info(f"Enviando petición ÚNICA y completa a Gemini para: {filename}")
    try:
        response = await model.generate_content_async(prompt)
        cleaned_response = response.text.strip().lstrip("```json").rstrip("```").strip()
        data = json.loads(cleaned_response)
        logger.info(f"Análisis completo de Gemini (lógica original) recibido exitosamente.")
        return data
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        logger.error(f"Error al decodificar la respuesta de Gemini: {e}", exc_info=True)
        logger.error(f"Respuesta recibida de Gemini que causó el error: {response.text}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado en la llamada a Gemini: {e}", exc_info=True)
        return None