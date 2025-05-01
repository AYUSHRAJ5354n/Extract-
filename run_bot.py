#!/usr/bin/env python3
"""
Entrypoint script for the Telegram bot workflow
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Check for Telegram bot token
if not os.environ.get("TELEGRAM_BOT_TOKEN"):
    logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
    print("Error: TELEGRAM_BOT_TOKEN environment variable is not set!")
    print("Please set it before running this script.")
    sys.exit(1)

# Import and run the Telegram bot
print("Starting Telegram bot...")
from telegram_bot import main

if __name__ == "__main__":
    main()