# main.py
import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import config
from handlers import HandlerManager

logger = logging.getLogger(__name__)

async def main() -> None:
    """Start the bot."""
    try:
        # Create the Application instance
        application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Initialize handlers
        handlers = HandlerManager()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", handlers.start_command))
        application.add_handler(CommandHandler("help", handlers.help_command))
        application.add_handler(CommandHandler("chat", handlers.chat_command))
        application.add_handler(CommandHandler("game", handlers.game_command))
        application.add_handler(CommandHandler("normal", handlers.normal_command))
        application.add_handler(CommandHandler("delete", handlers.delete_command))
        application.add_handler(CommandHandler("list", handlers.list_command))
        application.add_handler(CommandHandler("category", handlers.category_command))
        
        # Add message handler
        application.add_handler(MessageHandler(filters.TEXT | filters.VOICE, handlers.handle_message))
        
        # Add callback query handler
        application.add_handler(CallbackQueryHandler(handlers.handle_callback_query))
        
        # Start the bot
        logger.info("Starting bot...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Run the bot until it is interrupted
        logger.info("Bot started successfully!")
        await application.updater.stop()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")