import os
import asyncio
import random
from openai import OpenAI

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# ====== ENV ======
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN env yo'q. Render -> Environment variables ga qo'ying.")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY env yo'q. Render -> Environment variables ga qo'ying.")

client = OpenAI(api_key=OPENAI_API_KEY)

# ====== PERSONA (prank vibe, lekin o'zini odam deb ko'rsatmaydi) ======
SYSTEM_PROMPT = """
You are "Silicon Buddy" — witty, confident, slightly sarcastic, friendly.
Reply in Uzbek mostly (mix small English tech slang ok).
Keep replies short: 1–3 sentences.
Occasionally add a tiny emoji, not too many.

Safety rules:
- Never claim to be a real human. If asked, say you are an AI bot.
- Don't generate harassment, threats, or doxxing. If user asks for private info, refuse briefly.
- If topic becomes serious/sensitive, drop the jokes and be supportive.
"""

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.85"))

# Typing delay prank effect (seconds). Set 0 to disable.
TYPING_DELAY_MIN = float(os.getenv("TYPING_DELAY_MIN", "1.2"))
TYPING_DELAY_MAX = float(os.getenv("TYPING_DELAY_MAX", "3.5"))

# ====== COMMAND-LIKE SWITCHES ======
ROAST_ON_TEXT = "roast on"
ROAST_OFF_TEXT = "roast off"

ROAST_PROMPT_ADDON = """
Mode: ROAST (playful). Light teasing, never cruel. No insults about protected traits.
"""

CHILL_PROMPT_ADDON = """
Mode: CHILL. Be extra polite and calm.
"""

def clamp_history(history, max_items=12):
    return history[-max_items:] if len(history) > max_items else history

def ai_complete_sync(messages: list[dict]) -> str:
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=TEMPERATURE,
    )
    return (resp.choices[0].message.content or "").strip()

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("mode", "roast")
    await update.message.reply_text(
        "😄 Salom! Men Silicon Buddy — prank AI bot.\n"
        "Oddiy yozing, men javob beraman.\n\n"
        "🔥 Roast mode yoqish: `roast on`\n"
        "🧊 Chill mode: `roast off`",
        parse_mode="Markdown",
    )

# ====== MAIN MESSAGE HANDLER ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # Roast mode toggle (simple text commands)
    if text.lower() == ROAST_ON_TEXT:
        context.user_data["mode"] = "roast"
        await update.message.reply_text("🔥 Roast mode ON. Endi gapni kesaman (hazil) 😄")
        return

    if text.lower() == ROAST_OFF_TEXT:
        context.user_data["mode"] = "chill"
        await update.message.reply_text("🧊 Chill mode ON. Endi muloyimroqman 🙂")
        return

    # Small prank typing delay
    if TYPING_DELAY_MAX > 0:
        await asyncio.sleep(random.uniform(TYPING_DELAY_MIN, TYPING_DELAY_MAX))

    # Conversation memory per-user
    history = context.user_data.get("history", [])
    history.append({"role": "user", "content": text})
    history = clamp_history(history, 12)

    mode = context.user_data.get("mode", "roast")
    addon = ROAST_PROMPT_ADDON if mode == "roast" else CHILL_PROMPT_ADDON

    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n" + addon}] + history

    try:
        # OpenAI call in thread to avoid blocking event loop
        answer = await asyncio.to_thread(ai_complete_sync, messages)
        if not answer:
            answer = "Hmm… brain.exe qotib qoldi 😅 Qaytadan yoz."
    except Exception:
        answer = "Serverim biroz charchadi 😭 Keyinroq yozib ko‘r."

    history.append({"role": "assistant", "content": answer})
    context.user_data["history"] = clamp_history(history, 12)

    await update.message.reply_text(answer)

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # /start command
    app.add_handler(CommandHandler("start", start))

    # text messages (non-commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # run
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
