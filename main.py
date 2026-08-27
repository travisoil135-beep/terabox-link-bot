import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Aapka Bot Token yahan added hai
BOT_TOKEN = "8767544995:AAGAlinr9hXMHTEiYzsI6X0zvBRJtOzpWdc"

def get_terabox_direct_link(terabox_url: str):
    api_endpoint = f"https://terabox-api-v2.onrender.com/api?data={terabox_url}"
    try:
        response = requests.get(api_endpoint, timeout=10)
        data = response.json()
        if data.get("status") == "success" or "direct_link" in data:
            return {
                "title": data.get("file_name", "Video/File"),
                "download_link": data.get("direct_link"),
                "fast_link": data.get("fast_download_link", data.get("direct_link"))
            }
        return None
    except Exception:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\nMujhe koi bhi Terabox video/file ka link send karein, main direct fast link bana kar doonga."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "terabox" in text or "1024tera" in text or "teraboxapp" in text:
        status_msg = await update.message.reply_text("⏳ Processing... Link extract ho raha hai.")
        url_match = re.search(r'(https?://[^\s]+)', text)
        if not url_match:
            await status_msg.edit_text("❌ Sahi link nahi mila.")
            return

        target_url = url_match.group(0)
        result = get_terabox_direct_link(target_url)
        
        if result:
            reply_text = (
                f"🎬 Title: {result['title']}\n\n"
                f"🔗 Direct Download Link:\n{result['download_link']}\n\n"
                f"⚡ Fast Stream Link:\n{result['fast_link']}"
            )
            await status_msg.edit_text(reply_text)
        else:
            await status_msg.edit_text("❌ Link bypass nahi ho saka (Link invalid ya expired hai).")
    else:
        await update.message.reply_text("Kripya valid Terabox link bhejein.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()

if __name__ == "__main__":
    main()
