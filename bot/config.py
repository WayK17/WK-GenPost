# /bot/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Credenciales existentes
BOT_TOKEN = os.getenv("BOT_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

TMDB_API_URL = "https://api.themoviedb.org/3"

# Nuevas credenciales para Pyrogram
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Verificamos que todas las credenciales estén presentes
if not all([BOT_TOKEN, TMDB_API_KEY, GEMINI_API_KEY, API_ID, API_HASH]):
    raise ValueError("Faltan una o más credenciales en el archivo .env")

# Convertimos el API_ID a entero
API_ID = int(API_ID)