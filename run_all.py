#!/usr/bin/env python3
"""
Script to run both the web application and Telegram bot concurrently
"""

import os
import subprocess
import signal
import sys
import time

# Process globals
web_process = None
bot_process = None

def signal_handler(sig, frame):
    """Handle termination signals by cleaning up processes"""
    print('Shutting down processes...')
    if web_process:
        web_process.terminate()
    if bot_process:
        bot_process.terminate()
    sys.exit(0)

def main():
    """Start both the web application and Telegram bot"""
    global web_process, bot_process
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check if TELEGRAM_BOT_TOKEN is set
    if not os.environ.get('TELEGRAM_BOT_TOKEN'):
        print("Error: TELEGRAM_BOT_TOKEN environment variable is not set.")
        print("Please set it before running this script.")
        sys.exit(1)
    
    try:
        # Start web application (gunicorn)
        print("Starting web application...")
        port = os.environ.get('PORT', '5000')
        web_process = subprocess.Popen(
            ['gunicorn', '--bind', f'0.0.0.0:{port}', 'main:app'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Start Telegram bot
        print("Starting Telegram bot...")
        bot_process = subprocess.Popen(
            ['python', 'telegram_bot.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        print("Both services are now running!")
        print("Press Ctrl+C to stop all services.")
        
        # Monitor processes and their output
        while True:
            # Check if processes are still running
            if web_process.poll() is not None:
                print("Web application stopped unexpectedly. Restarting...")
                web_process = subprocess.Popen(
                    ['gunicorn', '--bind', f'0.0.0.0:{port}', 'main:app'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
            
            if bot_process.poll() is not None:
                print("Telegram bot stopped unexpectedly. Restarting...")
                bot_process = subprocess.Popen(
                    ['python', 'telegram_bot.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
            
            # Print output from web application
            try:
                web_output = web_process.stdout.readline()
                if web_output:
                    print(f"[Web] {web_output.strip()}")
            except:
                pass
                
            # Print output from Telegram bot
            try:
                bot_output = bot_process.stdout.readline()
                if bot_output:
                    print(f"[Bot] {bot_output.strip()}")
            except:
                pass
                
            # Sleep briefly to avoid high CPU usage
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()