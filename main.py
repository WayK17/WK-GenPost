# main.py
import logging
import asyncio
import os

from pyrogram import Client
from bot import config

# Importamos los componentes web de aiohttp
from aiohttp import web

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Lógica del Servidor Web para Health Check ---

async def health_check(request):
    """Responde al health check de Koyeb."""
    return web.Response(text="Nave Fénix operativa y en línea.")

async def start_web_server():
    """Inicia el servidor web de aiohttp."""
    app = web.Application()
    app.router.add_get("/", health_check)
    
    # Koyeb nos da el puerto a través de una variable de entorno
    port = int(os.getenv('PORT', 8080))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Servidor web de health check escuchando en el puerto {port}.")
    
    # Mantenemos el servidor corriendo
    while True:
        await asyncio.sleep(3600)

# --- Función Principal Asíncrona ---

async def main():
    """Inicia el cliente de Pyrogram y el servidor web en paralelo."""
    logger.info("Iniciando la nave Fénix con todos sus sistemas...")
    
    # Creamos el cliente de Pyrogram
    app = Client(
        "PostCreatorBot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
        plugins=dict(root="bot/modules")
    )
    
    # Iniciamos el bot y el servidor web concurrentemente
    await asyncio.gather(
        app.start(),
        start_web_server()
    )

    logger.info("Motor MTProto encendido y servidor web activo. Nave operativa.")
    
    # Mantenemos el proceso principal vivo
    await app.idle()

    # Apagamos el bot de forma segura al detener el proceso
    await app.stop()
    logger.info("Nave detenida.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Proceso de apagado iniciado.")
