#!/usr/bin/env python3
"""
Telegram Bot for extracting Dailymotion links from URLs
"""

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from extractor import extract_dailymotion_link
from utils import is_valid_url

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get token from environment variable
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    welcome_message = (
        f"Hi {user.first_name}! 👋\n\n"
        "Welcome to the Dailymotion Link Extractor Bot! 🎬\n\n"
        "Send me a link to a website that has embedded Dailymotion videos, "
        "and I'll extract the direct Dailymotion link for you.\n\n"
        "Supported sites include:\n"
        "- SeaTV/Perfect World episodes\n"
        "- We TV\n"
        "- Many other sites with embedded Dailymotion players\n\n"
        "Just send me a URL and I'll do the rest!"
    )
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_message = (
        "📌 *How to use the Dailymotion Link Extractor* 📌\n\n"
        "Simply send me a URL of a webpage containing Dailymotion videos.\n\n"
        "*Example:*\n"
        "https://seatv-24.xyz/perfect-world-episode-213-subtitle/\n\n"
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "I'll extract the direct Dailymotion link for easier viewing!"
    )
    await update.message.reply_text(help_message, parse_mode="Markdown")


async def extract_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Extract Dailymotion link from the URL."""
    message_text = update.message.text
    
    # Check if the message contains a URL
    if not is_valid_url(message_text):
        await update.message.reply_text(
            "⚠️ Please send a valid URL. The message should contain a link to a webpage with Dailymotion videos."
        )
        return
    
    # Notify the user that we're processing their request
    processing_message = await update.message.reply_text(
        "🔍 Processing your URL... This may take a moment."
    )
    
    try:
        # Extract the Dailymotion link
        result = extract_dailymotion_link(message_text)
        
        if result.get("success"):
            # Success! Send the extracted link
            dailymotion_link = result.get("link")
            await processing_message.edit_text(
                f"✅ Success! Here's your Dailymotion link:\n\n{dailymotion_link}"
            )
        else:
            # Failed to extract link
            error_message = result.get("error", "Unknown error occurred")
            await processing_message.edit_text(
                f"❌ Sorry, I couldn't extract a Dailymotion link from that URL.\n\n"
                f"Error: {error_message}"
            )
    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}")
        await processing_message.edit_text(
            "❌ An error occurred while processing your request. Please try again later."
        )


def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Handle messages that contain URLs
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, extract_link))

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting Telegram Bot...")
    print("Telegram Bot is now running!")
    print("The bot will respond to messages sent through Telegram.")
    print("You can now test the bot by sending URLs to it.")
    
    # Poll for updates with a longer timeout to reduce CPU usage
    application.run_polling(allowed_updates=Update.ALL_TYPES, poll_interval=1.0)


if __name__ == "__main__":
    main()