from dotenv import load_dotenv
load_dotenv()

import os
import json
import stripe
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

