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
async def generate_creative_description(title: str, overview: str) -> str:
    """
    Usa Gemini para generar una descripción creativa y atractiva.
    """
    prompt = f"""
    Basado en el título "{title}" y la siguiente sinopsis: "{overview}",
    escribe una descripción corta (2-3 frases), atractiva y con emojis para un post de Telegram.
    El tono debe ser emocionante y captar la atención. No incluyas la sinopsis original.
    """
    logger.info(f"Generando descripción creativa para: {title}")
    try:
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error al generar la descripción con Gemini: {e}")
        return "Una emocionante película/serie que no te puedes perder." # Respuesta de respaldo

        