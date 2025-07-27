# 🎬 Telegram Bot for Searching TMDb

A lightweight Telegram bot that lets you search for movies and TV shows using the [TMDb](https://www.themoviedb.org/) API. It returns rich, interactive results including synopsis, genres, runtime, trailers (if available), and related recommendations — all in Spanish.

---

## 🚀 Features

- 🔐 Access control: only specific Telegram users are allowed to use the bot.
- 🔎 Multi-type search (`movie`, `tv`) in Spanish (`es-ES`).
- 📌 Interactive results using inline buttons.
- 📝 Displays detailed metadata: title, release year, synopsis, duration, seasons/episodes (for series), status, rating, genres, and country of origin.
- 🎥 YouTube trailer link (if available).
- 🎞 Recommendations for related movies or series.
- 🖼️ Automatically sends the poster image (if available and short enough for Telegram captions).

---

## ⚙️ Configuration via `.env`

You can customize the bot's behavior and credentials using environment variables. Create a `.env` file based on the included `.env.example`:

```dotenv
TELEGRAM_TOKEN=your_bot_token_here
TMDB_API_KEY=your_tmdb_api_key_here
ALLOWED_USERS=username1,username2
