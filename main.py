import re
import requests
from urllib.parse import urlparse, parse_qs, quote

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================================================
# TELEGRAM BOT TOKEN
# =========================================================
# Yahan apna EXISTING Telegram bot token paste karo.
BOT_TOKEN = "8767544995:AAGAlinr9hXMHTEiYzsI6X0zvBRJtOzpWdc"


# =========================================================
# TeraBox domains
# =========================================================
TERABOX_DOMAINS = (
    "terabox.com",
    "1024terabox.com",
    "terabox.app",
    "teraboxshare.com",
    "teraboxlink.com",
    "terasharefile.com",
    "terafileshare.com",
    "terasharelink.com",
    "teraboxapp.com",
    "nephobox.com",
    "4funbox.com",
    "freeterabox.com",
    "momerybox.com",
)


# =========================================================
# HTTP session
# =========================================================
def make_session():
    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Connection": "keep-alive",
    })

    return session


# =========================================================
# Extract URL from Telegram message
# =========================================================
def extract_url(text: str):

    urls = re.findall(r"https?://[^\s<>'\"]+", text)

    for url in urls:

        url = url.rstrip(".,!?)]}")

        host = (urlparse(url).hostname or "").lower()

        if any(domain in host for domain in TERABOX_DOMAINS):
            return url

    return None


# =========================================================
# Extract shorturl/surl
# =========================================================
def extract_shorturl(url: str):

    parsed = urlparse(url)

    # /s/XXXXXXXX
    match = re.search(
        r"/s/(?:1)?([A-Za-z0-9_-]+)",
        parsed.path
    )

    if match:
        return match.group(1)

    # ?surl=XXXXXXXX
    query = parse_qs(parsed.query)

    if query.get("surl"):
        return query["surl"][0]

    return None


# =========================================================
# Find text between two strings
# =========================================================
def find_between(text, first, last):

    try:
        start = text.index(first) + len(first)
        end = text.index(last, start)

        return text[start:end]

    except ValueError:
        return None


# =========================================================
# Format file size
# =========================================================
def format_size(size):

    try:
        size = float(size)
    except:
        return "Unknown"

    if size <= 0:
        return "Unknown"

    units = [
        "Bytes",
        "KB",
        "MB",
        "GB",
        "TB"
    ]

    i = 0

    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1

    return f"{size:.2f} {units[i]}"


# =========================================================
# TeraBox extractor
# =========================================================
def bypass_terabox(url: str):

    session = make_session()

    try:

        # -------------------------------------------------
        # STEP 1
        # Open share page
        # -------------------------------------------------

        response = session.get(
            url,
            timeout=30,
            allow_redirects=True
        )

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"TeraBox page HTTP {response.status_code}"
            }

        final_url = response.url
        html = response.text

        # -------------------------------------------------
        # STEP 2
        # Get shorturl
        # -------------------------------------------------

        shorturl = extract_shorturl(final_url)

        if not shorturl:
            shorturl = extract_shorturl(url)

        if not shorturl:

            # Try HTML
            match = re.search(
                r'"shorturl"\s*:\s*"([^"]+)"',
                html
            )

            if match:
                shorturl = match.group(1)

        if not shorturl:
            return {
                "success": False,
                "error": "Share ID / shorturl nahi mila."
            }

        # -------------------------------------------------
        # STEP 3
        # Get jsToken
        # -------------------------------------------------

        jsToken = find_between(
            html,
            'fn%28%22',
            '%22%29'
        )

        if not jsToken:

            patterns = [
                r'"jsToken"\s*:\s*"([^"]+)"',
                r'jsToken\s*=\s*"([^"]+)"',
                r'jsToken=([^&"]+)',
            ]

            for pattern in patterns:

                match = re.search(pattern, html)

                if match:
                    jsToken = match.group(1)
                    break

        if not jsToken:
            return {
                "success": False,
                "error": (
                    "TeraBox jsToken nahi mila. "
                    "TeraBox ne page verification change ki ho sakti hai."
                )
            }

        # -------------------------------------------------
        # STEP 4
        # dp-logid
        # -------------------------------------------------

        dp_logid = find_between(
            html,
            "dp-logid=",
            "&"
        )

        if not dp_logid:
            dp_logid = "0"

        # -------------------------------------------------
        # STEP 5
        # Share list API
        # -------------------------------------------------

        api_url = "https://www.terabox.app/share/list"

        params = {
            "app_id": "250528",
            "web": "1",
            "channel": "0",
            "jsToken": jsToken,
            "dp-logid": dp_logid,
            "page": "1",
            "num": "50",
            "by": "name",
            "order": "asc",
            "site_referer": "",
            "shorturl": shorturl,
            "root": "1",
        }

        api_headers = {
            "User-Agent": session.headers["User-Agent"],
            "Accept": "application/json, text/plain, */*",
            "Referer": final_url,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.terabox.app",
        }

        api_response = session.get(
            api_url,
            params=params,
            headers=api_headers,
            timeout=30
        )

        if api_response.status_code != 200:
            return {
                "success": False,
                "error": (
                    f"TeraBox share API HTTP "
                    f"{api_response.status_code}"
                )
            }

        try:
            data = api_response.json()
        except ValueError:
            return {
                "success": False,
                "error": "TeraBox ne JSON response nahi diya."
            }

        # -------------------------------------------------
        # STEP 6
        # Check response
        # -------------------------------------------------

        if data.get("errno", 0) != 0:

            return {
                "success": False,
                "error": (
                    "TeraBox API error: "
                    + str(data.get("errmsg", data.get("errno")))
                )
            }

        file_list = data.get("list", [])

        if not file_list:

            return {
                "success": False,
                "error": (
                    "Is public link mein koi file nahi mili. "
                    "Link expired/private ho sakta hai."
                )
            }

        results = []

        # -------------------------------------------------
        # STEP 7
        # Process files
        # -------------------------------------------------

        for item in file_list:

            filename = (
                item.get("server_filename")
                or item.get("filename")
                or item.get("name")
                or "TeraBox File"
            )

            size = format_size(
                item.get("size", 0)
            )

            dlink = item.get("dlink")

            direct_link = None

            # -------------------------------------------------
            # Resolve dlink redirect
            # -------------------------------------------------

            if dlink:

                try:

                    head_response = session.head(
                        dlink,
                        allow_redirects=False,
                        timeout=20
                    )

                    direct_link = (
                        head_response.headers.get("Location")
                    )

                except Exception:
                    direct_link = None

            # If redirect didn't resolve, keep original dlink
            final_download = direct_link or dlink

            if final_download:

                results.append({
                    "title": filename,
                    "size": size,
                    "link": final_download
                })

        if not results:

            return {
                "success": False,
                "error": (
                    "File information mil gayi, "
                    "lekin download link generate nahi hua."
                )
            }

        return {
            "success": True,
            "files": results
        }

    except requests.Timeout:

        return {
            "success": False,
            "error": "TeraBox request timeout ho gayi."
        }

    except requests.RequestException as e:

        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }

    except Exception as e:

        return {
            "success": False,
            "error": f"Extractor error: {str(e)}"
        }


# =========================================================
# /start
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "Mujhe TeraBox ka public share link bhejein.\n\n"
        "Example:\n"
        "https://1024terabox.com/s/XXXXXXXX\n\n"
        "⏳ Main file ka naam, size aur available "
        "download link nikalne ki koshish karunga."
    )


# =========================================================
# Message handler
# =========================================================
async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    target_url = extract_url(text)

    if not target_url:

        await update.message.reply_text(
            "❌ Valid TeraBox link nahi mila.\n\n"
            "1024terabox.com ya terabox.com ka "
            "public share link bhejein."
        )

        return

    msg = await update.message.reply_text(
        "⏳ TeraBox link extract kiya ja raha hai...\n"
        "Please wait."
    )

    result = bypass_terabox(target_url)

    if not result.get("success"):

        await msg.edit_text(
            "❌ Link extract nahi ho saka.\n\n"
            f"Reason:\n{result.get('error', 'Unknown error')}\n\n"
            "⚠️ Public share link dobara check karein."
        )

        return

    files = result.get("files", [])

    await msg.delete()

    # -------------------------------------------------
    # Send results
    # -------------------------------------------------

    for index, file in enumerate(files, start=1):

        title = file["title"]
        size = file["size"]
        link = file["link"]

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⚡ Direct Download / Watch",
                    url=link
                )
            ]
        ])

        caption = (
            f"🎬 File #{index}\n\n"
            f"📁 Name: {title}\n"
            f"📦 Size: {size}\n\n"
            "👇 Neeche button par click karein."
        )

        try:

            await update.message.reply_text(
                caption,
                reply_markup=keyboard
            )

        except Exception as e:

            await update.message.reply_text(
                f"❌ Button create nahi ho saka.\n"
                f"Error: {str(e)}"
            )


# =========================================================
# Error handler
# =========================================================
async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "Telegram error:",
        context.error
    )


# =========================================================
# MAIN
# =========================================================
def main():

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    app.add_error_handler(
        error_handler
    )

    print(
        "🤖 TeraBox Telegram Bot started..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()

