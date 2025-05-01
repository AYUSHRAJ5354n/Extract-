# Dailymotion Link Extractor

A Python-based API service that extracts Dailymotion links from various streaming websites. The application includes both a web interface and a Telegram bot for extracting video links.

## Features

- Extract Dailymotion links from various websites including Lucifer Donghua, SeaTV, and more
- Web interface for easy link extraction
- Telegram bot integration for mobile-friendly extraction
- API endpoints for programmatic access
- Specialized extraction techniques for different websites
- Both browser-based and non-browser extraction methods
- Optimized for cloud deployment on platforms like Koyeb

## Requirements

- Python 3.9+
- Flask
- Selenium
- Python Telegram Bot
- Chrome/Chromium browser (for browser-based extraction)

## Local Development

1. Clone the repository
2. Install dependencies:
   ```
   pip install -e .
   ```
3. Set up environment variables:
   ```
   export TELEGRAM_BOT_TOKEN=your_telegram_token_here
   ```
4. Run the application:
   ```
   python run_all.py
   ```

## Deployment on Koyeb

This application is optimized for deployment on Koyeb's free tier. To deploy:

1. Create a new Koyeb account if you don't have one
2. Create a new application from Git repository
3. Add the following environment variables in the Koyeb dashboard:
   - `PORT`: 8080
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather

Koyeb will automatically use the provided Dockerfile and koyeb.yaml configuration to build and deploy the application.

### Deployment Files

- `Dockerfile`: Contains all the necessary configurations for building the container image
- `koyeb.yaml`: Contains the Koyeb-specific deployment configuration
- `Procfile`: Defines the processes to run (web app and Telegram bot)
- `start.sh`: Production startup script that runs both the web app and Telegram bot

## Usage

### Web Interface

1. Access the deployed application's URL
2. Enter the URL of a webpage containing a Dailymotion video
3. Click "Extract" to get the direct Dailymotion link

### Telegram Bot

1. Start a chat with your bot on Telegram
2. Send a URL of a webpage containing a Dailymotion video
3. The bot will reply with the extracted Dailymotion link

### API

Send a POST request to `/api/extract` with the following JSON body:
```json
{
  "url": "https://example.com/page-with-dailymotion-video"
}
```

## Supported Websites

- Lucifer Donghua
- SeaTV
- Perfect World sites
- WeTV
- And others with embedded Dailymotion videos

## License

MIT License