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


SEASON_TEMPLATE = """
{hashtags}

---
🔺 <b>{title} T{season:02d}</b>
---
🏆 | <b>Calidad:</b> {quality}
📺 | <b>Resolución:</b> <code>{resolution}</code>
💿 | <b>Episodios:</b> {episodes_count} (Completa)
⚖️ | <b>Peso Total:</b> ~{file_size}
🔊 | <b>Audio:</b> {audio_tracks}
💬 | <b>Subtítulos:</b> {subtitle_tracks}
📁 | <b>Formato:</b> {format}
---
"""

MOVIE_TEMPLATE = """
{hashtags}

---
🔺 <b>{title} ({year})</b>
---
🏆 | <b>Calidad:</b> {quality}
📺 | <b>Resolución:</b> <code>{resolution}</code>
⏳ | <b>Duración:</b> {runtime}
⚖️ | <b>Peso:</b> {file_size}
🔊 | <b>Audio:</b> {audio_tracks}
💬 | <b>Subtítulos:</b> {subtitle_tracks}
📁 | <b>Formato:</b> {format}
---
"""