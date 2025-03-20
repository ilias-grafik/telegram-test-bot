import os
import stripe
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler

# Configura il bot e Stripe
TOKEN = ("8048770790:AAHhxbJOU0unkZSsCMpOoCbCRJqb1VvROYw")

if not TOKEN:
    raise ValueError("❌ ERRORE: IL_TUO_BOT_TOKEN NON TROVATO! Assicurati di averlo impostato su Render.")
else:
    print(f"✅ Token caricato correttamente: {TOKEN}")

CHAT_ID_ADMIN = ("188685892")
STRIPE_SECRET_KEY = ("sk_test_51R2Y3xGhCywfxUMIYIkJYuf99XwXif3BqOylRScJdU9UyvPkr1n2mBfaUjoeocYxLmRl1qUxhENKw8SYYATWWH6m00FDWXeg90")
STRIPE_WEBHOOK_SECRET = ("whsec_FB1N3cRTlzPnMwi289TbHw06vzJiw7ko")
CHANNEL_LINK = ("https://t.me/+sO8O4qZSTVQxNGU0")
stripe.api_key = ("sk_test_51R2Y3xGhCywfxUMIYIkJYuf99XwXif3BqOylRScJdU9UyvPkr1n2mBfaUjoeocYxLmRl1qUxhENKw8SYYATWWH6m00FDWXeg90")

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

def main():
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
    main()
