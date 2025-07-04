from pyrogram import Client, filters
from pyrogram.types import Message

@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """
    Responde al comando /start.
    """
    await message.reply_text(
        f"¡Nave Fénix operativa, {message.from_user.mention}! 👋\n\n"
        "**Capacidades:**\n"
        "- Análisis de películas y episodios individuales.\n"
        "- Para temporadas completas, envíe un archivo de muestra con el caption: `Temporada X Completa`.\n\n"
        "A la espera de sus órdenes."
    )