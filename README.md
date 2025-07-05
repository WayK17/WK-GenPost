# ✨ WK-GenPost Bot ✨

<div align="center">
  <img src="https://iili.io/3Q8HbFs.jpg" alt="Project Banner" width="600"/>
</div>

<p align="center">
  <strong>Un bot de Telegram inteligente que transforma archivos de video en publicaciones elegantes y ricas en información, listas para compartir.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python" alt="Python version">
  <img src="https://img.shields.io/badge/Pyrogram-2.0-orange?style=for-the-badge&logo=telegram" alt="Pyrogram version">
  <img src="https://img.shields.io/badge/API-TMDb%20%7C%20Gemini-green?style=for-the-badge&logo=google-cloud" alt="APIs">
</p>

---

## 🚀 ¿Qué es WK-GenPost?

¿Cansado de crear posts manualmente para tu canal de películas o series? **WK-GenPost** es tu asistente personal. Simplemente envía un archivo de video y el bot hará la magia: lo analizará, buscará información oficial en bases de datos como **TMDb**, y generará una publicación con un formato impecable, incluyendo póster, sinopsis, detalles técnicos y hashtags.

El objetivo es simple: **automatizar lo tedioso para que puedas centrarte en compartir contenido de calidad.**

<div align="center">
  <img src="https://iili.io/3Q8HbFs.jpg" alt="Demo del Bot en Acción" width="400"/>
  <br>
  <em>Un vistazo al resultado final. Limpio, profesional y automático.</em>
</div>

---

## 🌟 Características Principales

Este bot fue diseñado pensando en la eficiencia y la estética.

* 🤖 **Análisis Inteligente:** Utiliza IA (Google Gemini) para entender el nombre del archivo, extrayendo el título, año, temporada y episodio con alta precisión.
* 🎬 **Integración Oficial con TMDb:** Se conecta con *The Movie Database* para obtener datos 100% fiables: pósters en alta resolución, sinopsis oficiales, listas de actores, directores y géneros.
* ✍️ **Formato Automático y Elegante:** Genera un texto de publicación perfectamente estructurado usando plantillas HTML. Olvídate de escribir manualmente la calidad, resolución o peso.
* 🔍 **Búsqueda Robusta y Tenaz:**
    * **Fallback a Inglés:** Si no encuentra un título en español, lo busca automáticamente en inglés.
    * **Limpieza de Títulos:** Normaliza los títulos eliminando "ruido" (`!`, `|`, etc.) para asegurar la máxima compatibilidad en la búsqueda.
    * **Reintentos Inteligentes:** Si la búsqueda con el título completo falla, lo intenta de nuevo con una versión más corta.
* 📄 **Páginas de Telegraph Detalladas:** Crea automáticamente una página en Telegraph con la sinopsis completa, elenco principal y más detalles, manteniendo tu post principal limpio y conciso.
* ✨ **Detección Automática de Calidad:** Identifica etiquetas como `BDRip`, `WEB-DL`, `WEBRip`, etc., directamente desde el nombre del archivo o el caption.

---

## 🛠️ Cómo Funciona (El Flujo Mágico)

El proceso está optimizado para ser rápido y eficiente, todo con una sola meta: un post perfecto en segundos.

1.  **Tú Envías un Archivo:** Simplemente arrastra y suelta un archivo de video en el chat con el bot.
2.  **El Bot Analiza:** Extrae metadatos técnicos (resolución, audios, subtítulos) y usa IA para entender el título.
3.  **Busca Información:** Con los datos extraídos, consulta TMDb para obtener pósters, sinopsis y más.
4.  **Crea el Post:** Ensambla toda la información en una plantilla elegante.
5.  **¡Listo!** Recibes una publicación perfecta, citando tu mensaje original.

---

## ⚙️ Configuración e Instalación

Poner en marcha tu propio WK-GenPost es muy sencillo.

### Prerrequisitos
* Python 3.10 o superior.
* Una cuenta de Telegram y tus credenciales de API (`API_ID` y `API_HASH`).
* Una clave de API de **Google Gemini**.
* Una clave de API de **TMDb**.
* Un token de bot de Telegram de **@BotFather**.

### Pasos de Instalación

1.  **Clona el repositorio:**
    ```bash
    git clone [https://github.com/tu-usuario/WK-GenPost.git](https://github.com/tu-usuario/WK-GenPost.git)
    cd WK-GenPost
    ```

2.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Crea tu archivo de configuración:**
    Crea un archivo llamado `.env` en la raíz del proyecto y añade tus claves.

    ```dotenv
    # / .env

    # Credenciales de Telegram
    API_ID=12345678
    API_HASH="tu_api_hash_aqui"
    BOT_TOKEN="tu_bot_token_aqui"

    # Claves de APIs Externas
    GEMINI_API_KEY="tu_gemini_api_key"
    TMDB_API_KEY="tu_tmdb_api_key"

    # Opcional: Para la creación de páginas de Telegraph anónimas
    # TELEGRAPH_TOKEN="" 
    ```

4.  **¡Ejecuta el bot!**
    ```bash
    python -m bot
    ```

---

## 🔮 Visión a Futuro: El Creador Interactivo

Este proyecto es la base. La próxima gran evolución es transformarlo en un **asistente de creación de posts totalmente interactivo**, donde el usuario pueda guiar al bot paso a paso, ajustar detalles y añadir botones personalizados. ¡El futuro es conversacional!

<br>

<p align="center">
  Hecho con ❤️ y mucho código por la comunidad.
</p>
