import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

load_dotenv()

API_KEY = os.environ.get("TMDB_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
MIN_EPISODE_SCORE = float(os.environ.get("MIN_EPISODE_SCORE", 8.5))

# Solo usuarios permitidos
USUARIOS_PERMITIDOS = set(os.environ.get("ALLOWED_USERS", "").split(","))

def solo_autorizados(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user or user.username not in USUARIOS_PERMITIDOS:
            return
        return await func(update, context)
    return wrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@solo_autorizados
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola 👋. Envíame el título de una película o serie para buscarla en TMDb.")

@solo_autorizados
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    url = f"https://api.themoviedb.org/3/search/multi?api_key={API_KEY}&language=es-ES&query={query}"
    response = requests.get(url).json()

    resultados = [r for r in response.get("results", []) if r.get("media_type") in ("movie", "tv")]

    if not resultados:
        await update.message.reply_text("❌ No se encontraron resultados.")
        return

    keyboard = []
    context.user_data['resultados'] = {}
    for i, r in enumerate(resultados[:10]):
        titulo = r.get("title") or r.get("name")
        fecha = r.get("release_date") or r.get("first_air_date") or "¿?"
        year = fecha[:4]
        movie_id = str(r.get("id"))

        context.user_data['resultados'][movie_id] = r

        keyboard.append([
            InlineKeyboardButton(f"{titulo} ({year})", callback_data=movie_id)
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Selecciona el resultado correcto:", reply_markup=reply_markup)

@solo_autorizados
async def mejores_episodios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    movie_id = query.data.split("_")[1]
    detalle = context.user_data['resultados'].get(movie_id)

    if not detalle or detalle.get("media_type") != "tv":
        await query.edit_message_text("⚠️ No se pudo encontrar la serie.")
        return

    # Obtener número de temporadas
    url = f"https://api.themoviedb.org/3/tv/{movie_id}?api_key={API_KEY}&language=es-ES"
    data = requests.get(url).json()
    num_temporadas = data.get("number_of_seasons", 0)

    mejores = []
    for temporada in range(1, num_temporadas + 1):
        temporada_url = f"https://api.themoviedb.org/3/tv/{movie_id}/season/{temporada}?api_key={API_KEY}&language=es-ES"
        resp = requests.get(temporada_url).json()
        for episodio in resp.get("episodes", []):
            score = episodio.get("vote_average", 0)
            if score >= MIN_EPISODE_SCORE:
                titulo = episodio.get("name")
                episodio_num = episodio.get("episode_number")
                imdb_rating = score  # Temporal, hasta conectar con IMDb real
                mejores.append(f"{detalle['name']} {temporada}x{episodio_num:02} - {imdb_rating:.1f} TMDb")

    if not mejores:
        await query.message.reply_text("❌ No se encontraron episodios que superen el umbral de puntuación.")
    else:
        await query.message.reply_text("⭐️ *Episodios destacados:*\n\n" + "\n".join(mejores), parse_mode="Markdown")


@solo_autorizados
async def mostrar_detalle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    movie_id = query.data
    resultado = context.user_data['resultados'].get(movie_id)

    if not resultado:
        await query.edit_message_text("⚠️ No se encontró la información de la película.")
        return

    media_type = resultado.get("media_type")
    detalle = {}
    texto_extra = ""

    if media_type == "movie":
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=es-ES"
        detalle = requests.get(url).json()
        duracion = detalle.get("runtime")
        texto_extra += f"\n⏱ Duración: {duracion} minutos" if duracion else ""
    elif media_type == "tv":
        url = f"https://api.themoviedb.org/3/tv/{movie_id}?api_key={API_KEY}&language=es-ES"
        detalle = requests.get(url).json()
        temporadas = detalle.get("number_of_seasons")
        episodios = detalle.get("number_of_episodes")
        estado = detalle.get("status", "Desconocido")
        duraciones = detalle.get("episode_run_time", [])
        duracion_media = f"{sum(duraciones)//len(duraciones)} min" if duraciones else "N/D"
        texto_extra += f"\n📅 Temporadas: {temporadas}\n🎮 Episodios: {episodios}\n📡 Estado: {estado}\n⏱ Duración media por episodio: {duracion_media}"
        if media_type == "tv":
        botones_extra = [
            [InlineKeyboardButton("📈 Ver mejores episodios", callback_data=f"mejores_{movie_id}")]
        ]
        extra_markup = InlineKeyboardMarkup(botones_extra)
        await query.message.reply_text("¿Quieres ver los episodios mejor valorados?", reply_markup=extra_markup)

    puntuacion = detalle.get("vote_average")
    votos = detalle.get("vote_count")
    if puntuacion and votos:
        texto_extra += f"\n⭐️ Valoración: {puntuacion:.1f} ({votos} votos)"

    generos = detalle.get("genres", [])
    if generos:
        lista_generos = ", ".join([g['name'] for g in generos])
        texto_extra += f"\n🎭 Géneros: {lista_generos}"

    paises = detalle.get("production_countries") or detalle.get("origin_country")
    if isinstance(paises, list) and paises:
        if isinstance(paises[0], dict):
            pais_origen = ", ".join([p['iso_3166_1'] for p in paises])
        else:
            pais_origen = ", ".join(paises)
        texto_extra += f"\n🌍 País de origen: {pais_origen}"

    titulo = resultado.get("title") or resultado.get("name")
    fecha = resultado.get("release_date") or resultado.get("first_air_date") or "¿?"
    year = fecha[:4]
    sinopsis = resultado.get("overview", "Sin sinopsis disponible.")
    poster_path = resultado.get("poster_path")
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

        # Obtener trailer si existe
    trailer_url = None
    videos_url = f"https://api.themoviedb.org/3/{media_type}/{movie_id}/videos?api_key={API_KEY}&language=es-ES"
    videos_response = requests.get(videos_url).json()
    for video in videos_response.get("results", []):
        if video.get("site") == "YouTube" and video.get("type") == "Trailer":
            trailer_url = f"https://www.youtube.com/watch?v={video['key']}"
            break

    texto = f"*{titulo}* ({year}){texto_extra}\n\n{sinopsis}"
    
    if trailer_url:
        texto += f"\n\n▶️ [Ver tráiler en YouTube]({trailer_url})"

    if poster_url and len(texto) <= 1024:
        await query.message.reply_photo(photo=poster_url, caption=texto, parse_mode="Markdown")
    else:
        if poster_url:
            await query.message.reply_photo(photo=poster_url)
        await query.message.reply_text(texto, parse_mode="Markdown")

    # Películas relacionadas
    recomendaciones = []
    if media_type == "movie":
        rec_url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations?api_key={API_KEY}&language=es-ES"
    elif media_type == "tv":
        rec_url = f"https://api.themoviedb.org/3/tv/{movie_id}/recommendations?api_key={API_KEY}&language=es-ES"
    else:
        rec_url = None

    if rec_url:
        rec_response = requests.get(rec_url).json()
        recomendaciones = rec_response.get("results", [])[:5]

    if recomendaciones:
        rec_keyboard = []
        for r in recomendaciones:
            rec_id = str(r["id"])
            rec_title = r.get("title") or r.get("name")
            rec_fecha = r.get("release_date") or r.get("first_air_date") or "¿?"
            rec_year = rec_fecha[:4]
            context.user_data['resultados'][rec_id] = r
            rec_keyboard.append([
                InlineKeyboardButton(f"{rec_title} ({rec_year})", callback_data=rec_id)
            ])

        rec_markup = InlineKeyboardMarkup(rec_keyboard)
        await query.message.reply_text("🎬 {} relacionadas:".format("Películas" if media_type == "movie" else "Series"), reply_markup=rec_markup)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buscar))
    app.add_handler(CallbackQueryHandler(mostrar_detalle))
    app.add_handler(CallbackQueryHandler(mejores_episodios, pattern=r"^mejores_\d+$"))
    app.add_error_handler(error_handler)

    app.run_polling()
