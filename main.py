# main.py
import logging
from pyrogram import Client
from bot import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Iniciando la nave Fénix...")

    # Creamos el cliente de Pyrogram
    app = Client(
        "PostCreatorBot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
        plugins=dict(root="bot/modules") # Importante: le decimos que busque nuestros handlers en esta carpeta
    )

    logger.info("Motor MTProto encendido. Nave operativa.")
    app.run()
    logger.info("Nave detenida.")