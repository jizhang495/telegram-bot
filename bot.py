import os
import random
import logging
from datetime import datetime, time, timedelta

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import openai
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-nano")
USER_CHAT_ID = os.environ.get("USER_CHAT_ID")
TIMEZONE = os.environ.get("TIMEZONE", "UTC")

if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY:
    raise SystemExit("Missing TELEGRAM_BOT_TOKEN or OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

tz = pytz.timezone(TIMEZONE)

async def gpt_reply(prompt: str) -> str:
    messages = [
        {"role": "system", "content": "You are a close female friend chatting in a warm, supportive tone."},
        {"role": "user", "content": prompt},
    ]
    try:
        resp = await openai.ChatCompletion.acreate(model=OPENAI_MODEL, messages=messages)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error("OpenAI error: %s", e)
        return "Sorry, I'm having trouble thinking right now."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    reply = await gpt_reply(user_text)
    await update.message.reply_text(reply)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey! I'm here whenever you want to chat.")

async def send_random_update(context: ContextTypes.DEFAULT_TYPE):
    chat_id = USER_CHAT_ID or context.job.chat_id
    prompt = "Share a short update or fun fact for the day in one or two sentences."
    msg = await gpt_reply(prompt)
    await context.bot.send_message(chat_id=chat_id, text=msg)

async def send_bedtime(context: ContextTypes.DEFAULT_TYPE):
    chat_id = USER_CHAT_ID or context.job.chat_id
    prompt = "Say goodnight and check in warmly in one or two sentences."
    msg = await gpt_reply(prompt)
    await context.bot.send_message(chat_id=chat_id, text=msg)

def schedule_daily_updates(application):
    job_queue = application.job_queue
    job_queue.scheduler.remove_all_jobs()
    now = datetime.now(tz)
    def random_time():
        start = datetime.combine(now.date(), time(8, 0, tzinfo=tz))
        end = datetime.combine(now.date(), time(20, 0, tzinfo=tz))
        delta = end - start
        random_minutes = random.randrange(int(delta.total_seconds() // 60))
        return (start + timedelta(minutes=random_minutes)).time()

    t1 = random_time()
    t2 = random_time()
    for t in sorted([t1, t2]):
        job_queue.run_daily(
            send_random_update,
            time=t,
            name=f"update_{t.hour}_{t.minute}",
            chat_id=USER_CHAT_ID,
        )
    job_queue.run_daily(
        send_bedtime,
        time=time(hour=22, minute=30),
        name="bedtime",
        chat_id=USER_CHAT_ID,
    )

    def reschedule(context: ContextTypes.DEFAULT_TYPE):
        schedule_daily_updates(context.application)

    job_queue.run_daily(
        reschedule,
        time=time(hour=0, minute=0),
        name="reschedule",
        chat_id=USER_CHAT_ID,
    )

async def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    schedule_daily_updates(application)
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
