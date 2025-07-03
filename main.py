import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Cambiamos las importaciones para que sean absolutas desde 'bot'
from bot import config
from bot import handlers

# Configura el logging para ver errores
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Definimos los Handlers de Comandos ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía un mensaje cuando el comando /start es ejecutado."""
    user = update.effective_user
    await update.message.reply_html(
        f"¡Hola, {user.mention_html()}! 👋\n\n"
        f"Soy tu asistente para crear posts. Envíame un archivo de video para comenzar."
    )

# --- Función Principal ---

def main() -> None:
    """Inicia el bot y lo mantiene corriendo."""
    logger.info("Iniciando bot...")

    # Crea la aplicación del bot con el token
    application = Application.builder().token(config.BOT_TOKEN).build()

    # --- Registramos todos los handlers ---
    # 1. Handler para el comando /start
    application.add_handler(CommandHandler("start", start))
    
    # 2. Handler para todos los archivos de video y documentos
    # Usamos un filtro para que solo reaccione a estos tipos de mensaje
    # Línea correcta
    application.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handlers.file_handler))

    # Inicia el bot (modo polling)
    logger.info("Bot iniciado y esperando mensajes...")
    application.run_polling()
    logger.info("Bot detenido.")


if __name__ == "__main__":
    main()