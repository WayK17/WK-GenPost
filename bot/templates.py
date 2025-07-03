# /bot/templates.py

DEFAULT_TEMPLATE = """
✨ **{title}** ({year}) ✨

{gemini_description}

---
🎬 **Detalles:**
- **Sinopsis:** _{overview}_
- **Géneros:** {genres}

⚙️ **Info. Técnica:**
- **Resolución:** {resolution}
- **Audio:** {audio_tracks}
- **Subtítulos:** {subtitle_tracks}
- **Peso:** {file_size}
"""

# Aquí podríamos añadir TEMPLATE_2, TEMPLATE_3, etc. en el futuro.