# 🎮 Telegram Bot para Buscar Películas y Series (en Español)

Un bot ligero para Telegram que te permite buscar películas y series usando la [API de TMDb](https://www.themoviedb.org/). Devuelve resultados interactivos y ricos en contenido, completamente en **español**, incluyendo sinopsis, géneros, duración, tráilers (si están disponibles), y recomendaciones relacionadas.

---

## 🚀 Funcionalidades

* 🔐 Control de acceso: solo usuarios de Telegram autorizados pueden usar el bot.
* 🔎 Búsqueda multi-tipo (`movie`, `tv`) en español (`es-ES`).
* 📌 Resultados interactivos mediante botones inline.
* 📝 Muestra metadatos detallados: título, año de estreno, sinopsis, duración, temporadas/episodios (para series), estado, puntuación, géneros y país de origen.
* 🎥 Enlace al tráiler en YouTube (si está disponible).
* 🎞 Recomendaciones de películas o series similares.
* 🖼 Envío automático del póster (si está disponible y cabe en la descripción de Telegram).

> 📌 **Nota:** Todos los resultados se devuelven en español (idioma `es-ES`). Se podría hacer configurable en futuras versiones.

---

## ⚙️ Configuración vía `.env`

Puedes personalizar el comportamiento del bot y sus credenciales mediante variables de entorno. Crea un archivo `.env` basado en el ejemplo:

```dotenv
TELEGRAM_TOKEN=your_bot_token_here
TMDB_API_KEY=your_tmdb_api_key_here
ALLOWED_USERS=username1,username2
```
⚠️ No subas tu .env real. Usa .env.example para compartir la estructura de configuración.

--- 

🐳 Docker

Este proyecto está disponible como imagen Docker precompilada en Docker Hub:

📦 Docker Hub: wandish/tmdb-telegram-bot

## Ejemplo de docker-compose.yml

```
version: "3.8"

services:
  tmdb-bot:
    image: wandish/tmdb-telegram-bot:latest
    container_name: tmdb-telegram-bot
    restart: unless-stopped
    env_file:
      - ./tmdb-telegram-bot_data/.env
