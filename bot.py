from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
import logging
import os

# Configura il bot di Telegram
TOKEN = "8048770790:AAHhxbJOU0unkZSsCMpOoCbCRJqb1VvROYw"
CHAT_ID_ADMIN = "188685892"
CHANNEL_LINK = "https://t.me/+sO8O4qZSTVQxNGU0"

# Stati della conversazione
DATI_UTENTE = range(1)

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Benvenuto! Usa /abbonati per iniziare.")

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
