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

# Render vars
PORT = int(os.getenv("PORT", "10000"))
PUBLIC_URL = (os.getenv("RENDER_EXTERNAL_URL", "") or os.getenv("PUBLIC_URL", "")).strip()
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram").strip()  # keep starting with /

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN yo'q")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY yo'q")
if not PUBLIC_URL:
    raise RuntimeError("RENDER_EXTERNAL_URL yoki PUBLIC_URL yo'q")

WEBHOOK_URL = f"{PUBLIC_URL}{WEBHOOK_PATH}"

client = OpenAI(api_key=OPENAI_API_KEY)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.85"))

TYPING_DELAY_MIN = float(os.getenv("TYPING_DELAY_MIN", "0.8"))
TYPING_DELAY_MAX = float(os.getenv("TYPING_DELAY_MAX", "2.5"))

SYSTEM_PROMPT = """
You are "Silicon Buddy" — witty, confident, slightly sarcastic, friendly.
Reply mostly in Uzbek (tiny English tech slang ok).
Keep replies short: 1–3 sentences. Add a small emoji sometimes.

Rules:
- Never claim to be a real human. If asked, say you are an AI bot.
- No doxxing/threats/harassment.
- If topic turns serious, be kind and stop joking.
"""

def _ai(messages):
    r = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=TEMPERATURE,
    )
    return (r.choices[0].message.content or "").strip()

async def handle_business_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram Business update’lari shu yerga keladi.
    Muhim: business_connection_id bilan reply qilish kerak.
    """
    bm = update.business_message
    if not bm or not bm.message or not bm.message.text:
        return

    text = bm.message.text.strip()
    business_connection_id = bm.business_connection_id
    chat_id = bm.message.chat_id  # shu chatga reply

    # prank typing delay
    if TYPING_DELAY_MAX > 0:
        await asyncio.sleep(random.uniform(TYPING_DELAY_MIN, TYPING_DELAY_MAX))

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]

    try:
        answer = await asyncio.to_thread(_ai, messages)
        if not answer:
            answer = "brain.exe qotdi 😅 Qaytadan yoz."
    except Exception as e:
        print("OPENAI_ERROR:", repr(e))
        answer = "AI hozir ulanmadi 😭 Keyinroq yoz."

    # MUHIM: business_connection_id bilan yuboriladi (siz nomingizdan)
    await context.bot.send_message(
        chat_id=chat_id,
        text=answer,
        business_connection_id=business_connection_id,
    )

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Faqat Business chatlar uchun handler
    app.add_handler(MessageHandler(filters.UpdateType.BUSINESS_MESSAGE, handle_business_message))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH.lstrip("/"),
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
