import os
import stripe
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackContext, ConversationHandler
)
from dotenv import load_dotenv
from flask import Flask  # 👈 Trucco per farlo sembrare un Web Service

# Flask app fittizia per Render
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot attivo"

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# ✅ Token del bot Telegram (INSERITO DIRETTAMENTE)
TOKEN = "8048770790:AAHhxbJOU0unkZSsCMpOoCbCRJqb1VvROYw"

# 🔐 Altri dati sensibili da .env
CHAT_ID_ADMIN = os.getenv("CHAT_ID_ADMIN")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
CHANNEL_LINK = os.getenv("CHANNEL_LINK")

# Configura Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Logging per debug
logging.basicConfig(level=logging.INFO)

# Stati della conversazione
DATI_UTENTE = range(1)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Benvenuto! Usa /abbonati per iniziare.")

async def abbonati(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': 'Abbonamento Sala Segnali'},
                'unit_amount': 100,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url="https://tuo_sito.com/success",
        cancel_url="https://tuo_sito.com/cancel",
        metadata={'telegram_id': user_id}
    )

    keyboard = [[InlineKeyboardButton("Clicca qui per pagare", url=session.url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Sottoscrivi l'abbonamento:", reply_markup=reply_markup)

async def dati(update: Update, context: CallbackContext):
    await update.message.reply_text("Per completare l'iscrizione, inviami i tuoi dati in questo formato:\n\nNome Cognome\nNumero di telefono")
    return DATI_UTENTE

async def ricevi_dati(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    dati_testo = update.message.text.strip()

    righe = dati_testo.split("\n")
    if len(righe) < 2:
        await update.message.reply_text("Formato errato! Per favore, invia i tuoi dati in questo formato:\n\nNome Cognome\nNumero di telefono")
        return DATI_UTENTE

    nome_cognome = righe[0]
    cellulare = righe[1]

    message = f"Nuovo abbonato:\nNome: {nome_cognome}\nTelefono: {cellulare}\nID Telegram: {user_id}"
    await context.bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)

    await update.message.reply_text(f"Grazie! Ecco il link per accedere: {CHANNEL_LINK}")
    return ConversationHandler.END

# 🔁 Configura e avvia il bot
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("abbonati", abbonati))
application.add_handler(CommandHandler("dati", dati))

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("dati", dati)],
    states={
        DATI_UTENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_dati)],
    },
    fallbacks=[],
)
application.add_handler(conv_handler)

if __name__ == "__main__":
    application.run_polling()
