# /bot/utils.py
import re

def clean_title_for_matching(title: str) -> str:
    """Limpia un título para una comparación robusta."""
    if not title:
        return ""
    # Convertir a minúsculas
    title = title.lower()
    # Quitar caracteres especiales y signos de puntuación
    title = re.sub(r'[^\w\s]', '', title)
    # Quitar espacios extra
    title = re.sub(r'\s+', '', title)
    return title