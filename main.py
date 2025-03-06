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
        print("\n🤖 Starting Personal Reflection Bot...\n")
        
        # Create the Application instance
        print("🔑 Initializing with Telegram token...")
        application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Initialize handlers
        print("🔧 Setting up message handlers...")
        handlers = HandlerManager()
        
        # Add command handlers
        print("📝 Registering command handlers...")
        application.add_handler(CommandHandler("start", handlers.start_command))
        application.add_handler(CommandHandler("help", handlers.help_command))
        application.add_handler(CommandHandler("chat", handlers.chat_command))
        application.add_handler(CommandHandler("game", handlers.game_command))
        application.add_handler(CommandHandler("normal", handlers.normal_command))
        application.add_handler(CommandHandler("delete", handlers.delete_command))
        application.add_handler(CommandHandler("list", handlers.list_command))
        application.add_handler(CommandHandler("category", handlers.category_command))
        
        # Add message handler
        print("💬 Registering message handlers...")
        application.add_handler(MessageHandler(filters.TEXT | filters.VOICE, handlers.handle_message))
        
        # Add callback query handler
        print("🔄 Registering callback query handler...")
        application.add_handler(CallbackQueryHandler(handlers.handle_callback_query))
        
        # Start the bot
        print("\n🚀 Initializing bot and starting polling...")
        logger.info("Starting bot...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        print("\n✅ Bot is now running! Press Ctrl+C to stop.")
        print("-------------------------------------------")
        
        # Run the bot until it is interrupted
        logger.info("Bot started successfully!")
        await application.updater.stop()
        
    except Exception as e:
        error_msg = f"Error starting bot: {e}"
        print(f"\n❌ {error_msg}")
        logger.error(error_msg)
        print("\nTroubleshooting tips:")
        print("1. Check if your environment variables are set correctly in .env file")
        print("2. Verify your internet connection")
        print("3. Make sure all API keys are valid")
        print("4. Check the logs for more detailed error information\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n\n👋 Bot stopped! Goodbye!")
        logger.info("Bot stopped!")