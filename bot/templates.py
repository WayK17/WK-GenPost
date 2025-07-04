# /bot/templates.py

DEFAULT_TEMPLATE = """{hashtags}
---
🔺 | <b>{series_title} - S{season:02d}E{episode:02d}</b> |
<i>{episode_title}</i>
---
✨ | <b>Calidad:</b> <code>{quality}</code>
📐 | <b>Resolución:</b> <code>{resolution}</code>
⏳ | <b>Duración:</b> <code>{runtime}</code>
📦 | <b>Peso:</b> <code>{file_size}</code>
🔊 | <b>Audio:</b> <code>{audio_tracks}</code>
💬 | <b>Subtítulos:</b> <code>{subtitle_tracks}</code>
📁 | <b>Formato:</b> <code>{format}</code>
---
📜 <b>SINOPSIS:</b>
<blockquote><a href="{synopsis_url}">Click Aquí</a></blockquote>

---
<a href="https://t.me/NESS_Cloud">Nᴇꜱꜱ Cʟᴏᴜᴅ</a>
"""


SEASON_TEMPLATE = """
{hashtags}
---
📺 | <b>{title} - S{season:02d}</b> | 🔥
---
✨ | <b>Calidad:</b> <code>{quality}</code>
📐 | <b>Resolución:</b> <code>{resolution}</code>
💿 | <b>Episodios:</b> {episodes_count} (Completa)
📦 | <b>Peso Total:</b> <code>~{file_size}</code>
🔊 | <b>Audio:</b> <code>{audio_tracks}</code>
💬 | <b>Subtítulos:</b> <code>{subtitle_tracks}</code>
📁 | <b>Formato:</b> <code>{format}</code>
---
📜 <b>SINOPSIS:</b>
<blockquote><a href="{synopsis_url}">Click Aquí</a></blockquote>
---
<a href="https://t.me/NESS_Cloud">Nᴇꜱꜱ Cʟᴏᴜᴅ</a>
"""

MOVIE_TEMPLATE = """
{hashtags}
---
🎬 | <b>{title} ({year})</b> | 🔥
---
✨ | <b>Calidad:</b> <code>{quality}</code>
📐 | <b>Resolución:</b> <code>{resolution}</code>
⏳ | <b>Duración:</b> <code>{runtime}</code>
📦 | <b>Peso:</b> <code>{file_size}</code>
🔊 | <b>Audio:</b> <code>{audio_tracks}</code>
💬 | <b>Subtítulos:</b> <code>{subtitle_tracks}</code>
📁 | <b>Formato:</b> <code>{format}</code>
---
📜 <b>SINOPSIS:</b>
<blockquote><a href="{synopsis_url}">Click Aquí</a></blockquote>
---
<a href="https://t.me/NESS_Cloud">Nᴇꜱꜱ Cʟᴏᴜᴅ</a>
"""