import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = "8767544995:AAGAlinr9hXMHTEiYzsI6X0zvBRJtOzpWdc"

def fetch_terabox_file(raw_url: str):
    # Short code extract karna
    match = re.search(r'/(?:s/|surl=)([a-zA-Z0-9_-]+)', raw_url)
    if not match:
        return None
    
    key = match.group(1)
    if not key.startswith("1"):
        surl = "1" + key
    else:
        surl = key

    # Working Aggregator Engine
    target_api = f"https://api.ytbvideolyrics.com/api/terabox?url=https://terabox.com/s/{surl}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://ytbvideolyrics.com/"
    }

    try:
        res = requests.get(target_api, headers=headers, timeout=20)
        data = res.json()
        
        # Format 1: Direct link list
        if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
            file_info = data["data"][0]
            return {
                "title": file_info.get("filename", "Video File"),
                "size": file_info.get("size", "N/A"),
                "link": file_info.get("download_link", file_info.get("url"))
            }
        
        # Format 2: Direct object
        if "download_link" in data:
            return {
                "title": data.get("file_name", "Video File"),
                "size": data.get("file_size", "N/A"),
                "link": data.get("download_link")
            }
            
    except Exception:
        pass

    # Alternative engine
    try:
        alt_url = f"https://terabox.hnn.workers.dev/api/get-info?shorturl={surl}"
        alt_res = requests.get(alt_url, headers=headers, timeout=20).json()
        if alt_res.get("ok") and "list" in alt_res and len(alt_res["list"]) > 0:
            item = alt_res["list"][0]
            return {
                "title": item.get("server_filename", "Video File"),
                "size": "N/A",
                "link": item.get("dlink")
            }
    except Exception:
        pass

    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Terabox Video Player Bot**\n\nMujhe koi bhi link bhejein, direct fast streaming link mil jayega."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if any(k in text for k in ["terabox", "1024tera", "teraboxapp", "terafileshare", "nephobox"]):
        msg = await update.message.reply_text("⏳ Bypass ho raha hai... (5-10 sec wait karein)")
        
        url_match = re.search(r'(https?://[^\s]+)', text)
        if not url_match:
            await msg.edit_text("❌ Sahi link nahi mila.")
            return

        res = fetch_terabox_file(url_match.group(0))
        
        if res and res.get("link"):
            keyboard = [[InlineKeyboardButton("▶️ Watch Online / Download", url=res["link"])]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            caption = (
                f"🎬 **File:** `{res['title']}`\n"
                f"📦 **Size:** `{res['size']}`\n\n"
                f"✅ **Link Ready!** Neeche diye gaye button par click karein:"
            )
            await msg.edit_text(caption, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await msg.edit_text("❌ Is waqt Terabox bypass server busy hai. Ek baar dobara try karein.")
    else:
        await update.message.reply_text("Kripya valid Terabox link bhejein.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
