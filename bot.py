import os
import asyncio
import random
from openai import OpenAI

from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)

# ===== ENV =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

PORT = int(os.getenv("PORT", "10000"))
PUBLIC_URL = (os.getenv("RENDER_EXTERNAL_URL", "") or os.getenv("PUBLIC_URL", "")).strip()
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram").strip()

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN yo'q")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY yo'q")
if not PUBLIC_URL:
    raise RuntimeError("PUBLIC URL yo'q (Render Web Service bo‘lishi kerak)")

if not WEBHOOK_PATH.startswith("/"):
    WEBHOOK_PATH = "/" + WEBHOOK_PATH

WEBHOOK_URL = f"{PUBLIC_URL}{WEBHOOK_PATH}"

print("Webhook URL:", WEBHOOK_URL)

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = "Reply in short witty Uzbek. You are AI."

def ai_call(text):
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return r.choices[0].message.content

async def handle_business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bm = update.business_message
    if not bm or not bm.message or not bm.message.text:
        return

    text = bm.message.text
    bc_id = bm.business_connection_id
    chat_id = bm.message.chat_id

    await asyncio.sleep(random.uniform(0.5, 2))

    try:
        answer = await asyncio.to_thread(ai_call, text)
    except Exception as e:
        print("AI ERROR:", e)
        answer = "AI ishlamayapti 😅"

    await context.bot.send_message(
        chat_id=chat_id,
        text=answer,
        business_connection_id=bc_id
    )

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.UpdateType.BUSINESS_MESSAGE, handle_business)
    )

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH[1:],
        webhook_url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
