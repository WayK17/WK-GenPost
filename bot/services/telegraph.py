# /bot/services/telegraph.py
import logging
from telegraph import Telegraph

logger = logging.getLogger(__name__)

# Inicializamos el cliente de Telegraph de forma global
telegraph_client = None

def get_telegraph_client():
    """
    Obtiene o crea el cliente de Telegraph de forma lazy.
    """
    global telegraph_client
    if telegraph_client is None:
        try:
            telegraph_client = Telegraph()
            telegraph_client.create_account(short_name='PostCreatorBot', author_name='Post Creator')
            logger.info("Cliente de Telegraph inicializado correctamente.")
        except Exception as e:
            logger.error(f"Error al inicializar Telegraph: {e}")
            return None
    return telegraph_client

def create_page(title: str, content: str) -> str | None:
    """
    Crea una nueva página en Telegraph y devuelve la URL.
    FUNCIÓN SÍNCRONA para usar con asyncio.to_thread()
    """
    logger.info(f"Creando página de Telegraph para: {title}")
    
    try:
        client = get_telegraph_client()
        if not client:
            logger.error("No se pudo obtener el cliente de Telegraph")
            return None
            
        response = client.create_page(
            title=title,
            html_content=content
        )
        
        url = response.get('url')
        if url:
            logger.info(f"Página de Telegraph creada exitosamente: {url}")
            return url
        else:
            logger.error("La respuesta de Telegraph no contiene URL")
            return None
            
    except Exception as e:
        logger.error(f"Error crítico al crear página de Telegraph: {e}", exc_info=True)
        return None