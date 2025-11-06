import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Token API bot Anda
TOKEN = "8386982089:AAE_167l-UrzCINv5mjUEfxbEmaGu8XFfyo"

# Fungsi untuk menangani perintah /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo!")

# Fungsi utama
def main():
    # Buat aplikasi bot
    application = ApplicationBuilder().token(TOKEN).build()

    # Tambahkan handler untuk perintah /start
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Jalankan bot
    application.run_polling()

if __name__ == "__main__":
    main()
