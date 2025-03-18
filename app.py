import os
import logging
import stripe
from flask import Flask, request, jsonify

# Configura Flask
app = Flask(__name__)

# Configura Stripe
STRIPE_SECRET_KEY = "sk_test_51R2Y3xGhCywfxUMIYIkJYuf99XwXif3BqOylRScJdU9UyvPkr1n2mBfaUjoeocYxLmRl1qUxhENKw8SYYATWWH6m00FDWXeg90"
STRIPE_WEBHOOK_SECRET = "whsec_FB1N3cRTlzPnMwi289TbHw06vzJiw7ko"
stripe.api_key = STRIPE_SECRET_KEY

@app.route("/")
def home():
    return "Server Flask attivo!"

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
        print(f"Pagamento ricevuto da {user_id}")

    return jsonify(success=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
