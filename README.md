A Telegram chatbot that:
- Replies using OpenAI GPT-4.1 nano.
- Sends 3 daily messages (2 random messages/day (8AM–8PM) with updates or fun facts; 1 bedtime message (e.g., 10:30PM) checking in or saying goodnight).
- Acts like a close friend.
- Runs easily on cloud (Google Cloud, etc).

Environment Variables:
```
TELEGRAM_BOT_TOKEN=...
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-nano
USER_CHAT_ID=...  # optional
TIMEZONE=Europe/London
```

## Running locally
Install dependencies (requires `openai==0.28`) and start the bot:
```bash
pip install -r requirements.txt
python bot.py
```

## Deploying on Google Cloud Run
Build and deploy the container:
```bash
docker build -t telegram-bot .
# then push to a registry and deploy using gcloud run deploy
```
