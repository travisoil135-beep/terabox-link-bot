import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = "8767544995:AAGAlinr9hXMHTEiYzsI6X0zvBRJtOzpWdc"

def extract_terabox_id(url: str):
    match = re.search(r'/s/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    # Direct query param check
    match_surl = re.search(r'surl=([a-zA-Z0-9_-]+)', url)
    if match_surl:
        return match_surl.group(1)
    return None

def get_direct_download(target_url: str):
    share_id = extract_terabox_id(target_url)
    if not share_id:
        return None

    # Multi-Engine Endpoints for bypass
    endpoints = [
        f"https://ytshorts.savetube.me/api/v1/terabox-downloader?url={target_url}",
        f"https://api.syndicate.workers.dev/terabox?url={target_url}",
        f"https://teradl-api.dapuntaratya.com/generate_file?id={share_id}"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    for ep in endpoints:
        try:
            res = requests.get(ep, headers=headers, timeout=12)
            if res.status_code == 200:
                data = res.json()
                
                # Format 1
                if "response" in data and isinstance(data["response"], list) and len(data["response"]) > 0:
                    item = data["response"][0]
                    return {
                        "title": item.get("title", "Video File"),
                        "link": item.get("resolutions", {}).get("Fast Download", item.get("download_link"))
                    }
                
                # Format 2
                if "download_url" in data:
                    return {
                        "title": data.get("file_name", "Video File"),
                        "link": data.get("download_url")
                    }
                
                # Format 3
                if "direct_link" in data:
                    return {
                        "title": data.get("title", "Video File"),
                        "link": data.get("direct_link")
                    }
        except Exception:
            continue

    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\nMujhe koi bhi Terabox link bhejein, direct stream/download link mil jayega."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if any(k in text for k in ["terabox", "1024tera", "teraboxapp", "terafileshare", "4funbox", "mirrobox"]):
        msg = await update.message.reply_text("⚡ Fast link banaya ja raha hai...")
        
        url_match = re.search(r'(https?://[^\s]+)', text)
        if not url_match:
            await msg.edit_text("❌ Valid link nahi mila.")
            return

        url = url_match.group(0)
        data = get_direct_download(url)
        
        if data and data.get("link"):
            reply = (
                f"🎬 **File:** {data['title']}\n\n"
                f"⚡ **Direct Fast Link:**\n{data['link']}"
            )
            await msg.edit_text(reply)
        else:
            await msg.edit_text("❌ Is file ka direct link block/private hai ya expired ho chuka hai.")
    else:
        await update.message.reply_text("Kripya koi Terabox link bhejein.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
