#!/bin/bash
# Script to start the Telegram bot in production

# Check if TELEGRAM_BOT_TOKEN is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "WARNING: TELEGRAM_BOT_TOKEN environment variable is not set. Telegram bot will not function properly."
    echo "Please set this secret in your Koyeb dashboard."
    exit 1
fi

echo "Starting Telegram bot with token ${TELEGRAM_BOT_TOKEN:0:3}... (token truncated for security)"
python telegram_bot.py