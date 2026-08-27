import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = "8767544995:AAGAlinr9hXMHTEiYzsI6X0zvBRJtOzpWdc"

def get_terabox_direct_link(terabox_url: str):
    # Multi-API resolver fallback
    api_url = f"https://terabox-dl.qtcloud.workers.dev/api/get-info?url={terabox_url}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        data = response.json()
        
        # Check qtcloud response
        if data.get("ok") and "downloadUrl" in data:
            return {
                "title": data.get("filename", "Video/File"),
                "download_link": data.get("downloadUrl"),
                "fast_link": data.get("downloadUrl")
            }
        
        # Backup API
        fallback_api = f"https://terabox-videodownloader.online/api/fetch?url={terabox_url}"
        fb_res = requests.get(fallback_api, headers=headers, timeout=15).json()
        if fb_res.get("download_link"):
            return {
                "title": fb_res.get("title", "Video/File"),
                "download_link": fb_res.get("download_link"),
                "fast_link": fb_res.get("download_link")
            }
            
        return None
    except Exception:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\nMujhe koi bhi Terabox video/file ka link send karein, main direct link nikal kar doonga."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if any(domain in text for domain in ["terabox", "1024tera", "teraboxapp", "terafileshare", "nephobox"]):
        status_msg = await update.message.reply_text("⏳ Processing... Link extract ho raha hai.")
        url_match = re.search(r'(https?://[^\s]+)', text)
        if not url_match:
            await status_msg.edit_text("❌ Sahi link nahi mila.")
            return

        target_url = url_match.group(0)
        result = get_terabox_direct_link(target_url)
        
        if result:
            reply_text = (
                f"🎬 **Title:** {result['title']}\n\n"
                f"⚡ **Direct Fast Link:**\n{result['download_link']}"
            )
            await status_msg.edit_text(reply_text, parse_mode="Markdown")
        else:
            await status_msg.edit_text("❌ Link extract nahi ho saka. Yeh file private ho sakti hai ya server busy hai.")
    else:
        await update.message.reply_text("Kripya valid Terabox link bhejein.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()

if __name__ == "__main__":
    main()
