#!/bin/bash
# Script to start both the web app and Telegram bot in production

# Set default port if not provided
export PORT=${PORT:-8080}
echo "Using port: $PORT for web application"

# Start Xvfb for headless Chrome
echo "Starting Xvfb for headless browser support..."
Xvfb :99 -screen 0 1280x1024x24 > /dev/null 2>&1 &
export DISPLAY=:99

# Print environment info
echo "Starting application with:"
echo "- Python: $(python --version)"
echo "- Chrome: $(google-chrome-stable --version)"
echo "- ChromeDriver: $(chromedriver --version)"

# Start both processes
echo "Starting web application on port $PORT..."
gunicorn --bind 0.0.0.0:$PORT --workers 1 main:app &
WEB_PID=$!

echo "Starting Telegram bot..."
python telegram_bot.py &
BOT_PID=$!

# Function to handle shutdown
cleanup() {
    echo "Shutting down..."
    kill -TERM $WEB_PID $BOT_PID 2>/dev/null
    exit 0
}

# Set trap for clean shutdown
trap cleanup SIGINT SIGTERM

# Wait for either process to exit
wait -n $WEB_PID $BOT_PID

# If we get here, one of the processes exited
echo "One of the processes exited. Shutting down all processes..."
cleanup