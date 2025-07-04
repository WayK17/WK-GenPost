# /bot/services/telegraph.py
import logging
from telegraph import Telegraph

logger = logging.getLogger(__name__)

# Inicializamos el cliente de Telegraph. Puedes usar el nombre de tu bot.
# La primera vez que se ejecute, creará una cuenta para el bot.
telegraph = Telegraph()
telegraph.create_account(short_name='PostCreatorBot')

async def create_page(title: str, content: str) -> str | None:
    """
    Crea una nueva página en Telegraph y devuelve la URL.
    """
    logger.info(f"Creando página de Telegraph para: {title}")
    try:
        response = telegraph.create_page(
            title=title,
            html_content=content
        )
        return response['url']
    except Exception as e:
        logger.error(f"No se pudo crear la página de Telegraph: {e}")
        return None