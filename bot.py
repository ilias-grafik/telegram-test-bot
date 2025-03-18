import os
import logging
import sqlite3
import stripe
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Configura il bot e Stripe
TOKEN = "7864182809:AAHx7TV91gGUhqLU-q_2RP27KIBFNmDxS8U"
STRIPE_SECRET_KEY = "sk_test_51R2Y3xGhCywfxUMIYIkJYuf99XwXif3BqOylRScJdU9UyvPkr1n2mBfaUjoeocYxLmRl1qUxhENKw8SYYATWWH6m00FDWXeg90"
STRIPE_WEBHOOK_SECRET = "LA_TUA_SECRET_WEBHOOK_KEY"
CHANNEL_LINK = "https://t.me/+sO8O4qZSTVQxNGU0"

stripe.api_key = STRIPE_SECRET_KEY

# Inizializza database
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            nome_cognome TEXT,
            cellulare TEXT,
            ha_pagato INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Salva i dati utente
def salva_utente(telegram_id, nome_cognome, cellulare=None):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO utenti (telegram_id, nome_cognome, cellulare) VALUES (?, ?, ?)",
                   (telegram_id, nome_cognome, cellulare))
    conn.commit()
    conn.close()

# Segna pagamento completato
def conferma_pagamento(telegram_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE utenti SET ha_pagato = 1 WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()

# Controlla se un utente ha pagato
def ha_pagato(telegram_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ha_pagato FROM utenti WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

# Comando /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Benvenuto! Usa /abbonati per iniziare.")

# Comando /abbonati
def abbonati(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    if ha_pagato(user_id):
        update.message.reply_text("Hai già effettuato il pagamento! Usa /dati per completare l'iscrizione.")
        return
    
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
    user_id = update.message.from_user.id
    
    if not ha_pagato(user_id):
        update.message.reply_text("Devi prima effettuare il pagamento con /abbonati")
        return
    
    update.message.reply_text("Inserisci il tuo Nome e Cognome:")
    return "NOME_COGNOME"

# Ricezione nome e cognome
def ricevi_nome(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    nome_cognome = update.message.text
    salva_utente(user_id, nome_cognome)
    update.message.reply_text("Ora inserisci il tuo numero di cellulare:")
    return "CELLULARE"

# Ricezione cellulare
def ricevi_cellulare(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    cellulare = update.message.text
    salva_utente(user_id, None, cellulare)
    update.message.reply_text(f"Grazie! Ecco il link per accedere: {CHANNEL_LINK}")

# Server Flask per i Webhook
app = Flask(__name__)

@app.route("/webhook-stripe", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["telegram_id"]
        conferma_pagamento(user_id)

    return jsonify(success=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("abbonati", abbonati))
    application.add_handler(CommandHandler("dati", dati))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_nome))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_cellulare))
    
    application.run_polling()
    app.run(port=5000)
