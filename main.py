import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = "8767544995:AAGAlinr9hXMHTEiYzsI6X0zvBRJtOzpWdc"

def bypass_terabox(url: str):
    # Step 1: Resolve redirects agar short domain ho
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    })

    try:
        # Extract surl / key
        clean_url = url.strip()
        match = re.search(r'/(?:s/|surl=)([a-zA-Z0-9_-]+)', clean_url)
        if not match:
            return None
        
        short_id = match.group(1)
        if short_id.startswith("1"):
            short_id = short_id[1:]  # surl standard format

        # Primary Fast API Server
        api_url = f"https://teraboxvideodownloader.pro/api/fetch?url=https://terabox.com/s/1{short_id}"
        resp = session.get(api_url, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            if "download_link" in data or "dlink" in data:
                return {
                    "title": data.get("title", data.get("file_name", "Terabox Video")),
                    "size": data.get("size", "N/A"),
                    "link": data.get("download_link", data.get("dlink"))
                }
            if isinstance(data, list) and len(data) > 0:
                return {
                    "title": data[0].get("title", "Video File"),
                    "size": data[0].get("size", "N/A"),
                    "link": data[0].get("download_link")
                }

        # Secondary Rapid Backup
        backup_url = f"https://api.freeterabox.workers.dev/?url={clean_url}"
        b_resp = session.get(backup_url, timeout=15)
        if b_resp.status_code == 200:
            b_data = b_resp.json()
            if "download_url" in b_data:
                return {
                    "title": b_data.get("file_name", "Video File"),
                    "size": b_data.get("size", "N/A"),
                    "link": b_data.get("download_url")
                }

        return None
    except Exception:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Welcome!**\n\nMujhe koi bhi Terabox video link bhejein, direct fast link foran generate ho jayega."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if any(domain in text for domain in ["terabox", "1024tera", "teraboxapp", "terafileshare", "nephobox", "4funbox"]):
        msg = await update.message.reply_text("⏳ Link extract kiya ja raha hai...")
        
        url_match = re.search(r'(https?://[^\s]+)', text)
        if not url_match:
            await msg.edit_text("❌ Link detect nahi hua.")
            return

        target_url = url_match.group(0)
        res = bypass_terabox(target_url)
        
        if res and res.get("link"):
            button = InlineKeyboardMarkup([[InlineKeyboardButton("⚡ Direct Download / Watch", url=res["link"])]])
            caption = f"🎬 **Title:** `{res['title']}`\n📦 **Size:** `{res['size']}`"
            await msg.edit_text(caption, reply_markup=button, parse_mode="Markdown")
        else:
            await msg.edit_text("❌ Terabox server ne response deny kiya. Link re-check karein ya public link use karein.")
    else:
        await update.message.reply_text("Kripya valid Terabox URL send karein.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
