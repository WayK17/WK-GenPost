# /bot/templates.py

DEFAULT_TEMPLATE = """
✨ <b>{title}</b> ({year})

{gemini_description}
---
🎬 <b>Detalles:</b>
<i>{overview}</i>

- <b>Géneros:</b> {genres}
---
⚙️ <b>Info. Técnica:</b>
- <b>Resolución:</b> <code>{resolution}</code>
- <b>Audio:</b> <code>{audio_tracks}</code>
- <b>Subtítulos:</b> <code>{subtitle_tracks}</code>
- <b>Peso:</b> <code>{file_size}</code>
"""