from dotenv import load_dotenv
load_dotenv()

import os
import json
import stripe
from flask import Flask, request, jsonify
from telegram import Bot

# 🔐 Dati sensibili dalle variabili d'ambiente
import os

TELEGRAM_BOT_TOKEN = "8048770790:AAHhxbJOU0unkZSsCMpOoCbCRJqb1VvROYw"
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
CHANNEL_ID = os.environ.get("https://t.me/+u-pC91RnQl82MDNk")  # Deve essere negativo, es. -100xxxxxxxxxx

stripe.api_key = STRIPE_SECRET_KEY
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# 📁 File JSON per salvare gli abbonati
DB_FILE = "abbonati.json"

def carica_abbonati():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def salva_abbonati(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def aggiorna_utente(telegram_id, attivo):
    data = carica_abbonati()
    if str(telegram_id) not in data:
        data[str(telegram_id)] = {"attivo": attivo}
    else:
        data[str(telegram_id)]["attivo"] = attivo
    salva_abbonati(data)

def rimuovi_dal_gruppo(telegram_id):
    try:
        bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=telegram_id)
        bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=telegram_id)  # Unban immediato = rimozione
    except Exception as e:
        print(f"Errore nella rimozione dell'utente: {e}")

def aggiungi_al_gruppo(telegram_id):
    pass  # Solo l'utente può unirsi tramite link d'invito dopo il pagamento

# 🚀 Flask app per i webhook
app = Flask(__name__)

@app.route("/webhook-stripe", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        print(f"⚠️ Webhook signature error: {e}")
        return jsonify(success=False), 400

    event_type = event.get("type")

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        telegram_id = session.get("metadata", {}).get("telegram_id")
        if telegram_id:
            aggiorna_utente(telegram_id, attivo=True)
            print(f"✅ Pagamento completato per utente {telegram_id}")

    elif event_type == "invoice.payment_succeeded":
        subscription = event["data"]["object"]
        telegram_id = subscription.get("metadata", {}).get("telegram_id")
        if telegram_id:
            aggiorna_utente(telegram_id, attivo=True)
            print(f"🔁 Rinnovo riuscito per utente {telegram_id}")

    elif event_type in ["invoice.payment_failed", "customer.subscription.deleted"]:
        subscription = event["data"]["object"]
        telegram_id = subscription.get("metadata", {}).get("telegram_id")
        if telegram_id:
            aggiorna_utente(telegram_id, attivo=False)
            rimuovi_dal_gruppo(int(telegram_id))
            print(f"❌ Abbonamento terminato per utente {telegram_id}")

    return jsonify(success=True)

@app.route("/")
def home():
    return "Bot e Webhook attivi!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    