import os
import logging
import stripe
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler

# Configura il bot e Stripe
TOKEN = "8048770790:AAHhxbJOU0unkZSsCMpOoCbCRJqb1VvROYw"
CHAT_ID_ADMIN = "188685892"
STRIPE_SECRET_KEY = "sk_test_51R2Y3xGhCywfxUMIYIkJYuf99XwXif3BqOylRScJdU9UyvPkr1n2mBfaUjoeocYxLmRl1qUxhENKw8SYYATWWH6m00FDWXeg90"
STRIPE_WEBHOOK_SECRET = "whsec_FB1N3cRTlzPnMwi289TbHw06vzJiw7ko"
CHANNEL_LINK = "https://t.me/+sO8O4qZSTVQxNGU0"

stripe.api_key = STRIPE_SECRET_KEY

# Stati della conversazione
DATI_UTENTE = range(1)

# Comando /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Benvenuto! Usa /abbonati per iniziare.")

# Comando /abbonati
def abbonati(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': 'Abbonamento Sala Segnali'},
                'unit_amount': 10000,
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
    update.message.reply_text("Sottoscrivi l'abbonamento:", reply_markup=reply_markup)

# Comando /dati
def dati(update: Update, context: CallbackContext):
    update.message.reply_text("Per completare l'iscrizione, inviami i tuoi dati in questo formato:\n\nNome Cognome\nNumero di telefono")
    return DATI_UTENTE

# Ricezione dati utente
def ricevi_dati(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    dati_testo = update.message.text.strip()
    
    # Controlla se il formato è corretto
    righe = dati_testo.split("\n")
    if len(righe) < 2:
        update.message.reply_text("Formato errato! Per favore, invia i tuoi dati in questo formato:\n\nNome Cognome\nNumero di telefono")
        return DATI_UTENTE
    
    nome_cognome = righe[0]
    cellulare = righe[1]
    
    # Invia i dati direttamente alla chat dell'amministratore
    message = f"Nuovo abbonato:\nNome: {nome_cognome}\nTelefono: {cellulare}\nID Telegram: {user_id}"
    context.bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)
    
    # Invia il link di accesso al canale
    update.message.reply_text(f"Grazie! Ecco il link per accedere: {CHANNEL_LINK}")
    return ConversationHandler.END

# Server Flask per i Webhook
app = Flask(__name__)

@app.route("/webhook-stripe", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return str(e), 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["telegram_id"]
        
        # Informa l'utente che può inviare i dati
        bot = context.bot
        bot.send_message(chat_id=user_id, text="Pagamento ricevuto! Ora digita /dati e invia i tuoi dati.")
    
    return jsonify(success=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("abbonati", abbonati))
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("dati", dati)],
        states={
            DATI_UTENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_dati)],
        },
        fallbacks=[],
    )
    application.add_handler(conv_handler)
    
    application.run_polling()
    app.run(port=5000)

from threading import Thread

def run_telegram_bot():
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

    application.run_polling()

if __name__ == "__main__":
    Thread(target=run_telegram_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
