from flask import Flask, request
import stripe
import telegram

# Configura Flask
app = Flask(__name__)

# Configura il bot di Telegram
TOKEN = "8048770790:AAHhxbJOU0unkZSsCMpOoCbCRJqb1VvROYw"
CHAT_ID_ADMIN = "188685892"
bot = telegram.Bot(token=TOKEN)

# Configura Stripe
stripe.api_key = "sk_test_51R2Y3xGhCywfxUMIYIkJYuf99XwXif3BqOylRScJdU9UyvPkr1n2mBfaUjoeocYxLmRl1qUxhENKw8SYYATWWH6m00FDWXeg90"
WEBHOOK_SECRET = "whsec_FB1N3cRTlzPnMwi289TbHw06vzJiw7ko"

@app.route("/")
def home():
    return "Bot attivo!"

@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception as e:
        return str(e), 400

    # Verifica pagamento
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_email")

        # Invia messaggio al bot
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=f"Nuovo abbonato: {customer_email}")
        return "Success", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
