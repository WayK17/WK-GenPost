# /bot/config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Nueva línea

if not BOT_TOKEN:
    raise ValueError("No se encontró el BOT_TOKEN.")
if not TMDB_API_KEY:
    raise ValueError("No se encontró el TMDB_API_KEY.")
if not GEMINI_API_KEY:
    raise ValueError("No se encontró el GEMINI_API_KEY.")