import asyncio
import threading
import os
from bot.bot import PulseForgeBot
from web.app import create_app, socketio
from utils.logger import setup_logger

logger = setup_logger(__name__)

def run_web_server():
    """Run the Flask web server in a separate thread"""
    app = create_app()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)

async def run_bot():
    """Run the Discord bot"""
    bot = PulseForgeBot()
    try:
        await bot.start(os.getenv('DISCORD_TOKEN'))
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")

def main():
    """Main entry point"""
    logger.info("Starting PulseForge Bot and Web Dashboard...")
    
    # Check if Discord token is available
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token:
        logger.warning("No DISCORD_TOKEN found. Running web dashboard only.")
        logger.info("To enable Discord bot, set DISCORD_TOKEN environment variable.")
    
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=False)
    web_thread.start()
    
    # Start the bot only if token is available
    if discord_token:
        try:
            asyncio.run(run_bot())
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Application error: {e}")
    else:
        # Keep the web server running
        try:
            web_thread.join()
        except KeyboardInterrupt:
            logger.info("Shutting down web server...")

if __name__ == "__main__":
    main()
