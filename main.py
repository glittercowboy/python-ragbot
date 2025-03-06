# main.py
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import config
from handlers import HandlerManager

logger = logging.getLogger(__name__)

# Simple echo handler for testing
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    print(f"Echo received: {update.message.text}")
    await update.message.reply_text(f"You said: {update.message.text}")

# Error handler
async def error_handler(update, context):
    """Log Errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}")
    print(f"❌ Error in update {update}: {context.error}")

async def test_database_connection():
    """Test database connectivity before starting the bot."""
    try:
        print("🧪 Testing database connection...")
        from database import DatabaseService
        
        # Create a temporary database service to test connectivity
        db_service = DatabaseService()
        
        print("✅ Database connection test successful!")
        return True
    except Exception as e:
        error_msg = f"Database connection test failed: {e}"
        print(f"\n❌ {error_msg}")
        logger.error(error_msg)
        return False

async def main() -> None:
    """Start the bot."""
    try:
        print("\n🤖 Starting Personal Reflection Bot...\n")
        
        # Test database connection before proceeding
        db_test_success = await test_database_connection()
        if not db_test_success:
            print("❌ Cannot continue without database connection")
            return
        
        # Create the Application instance
        print("\n🔑 Initializing with Telegram token...")
        application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Add error handler
        print("🛠️ Setting up error handler...")
        application.add_error_handler(error_handler)
        
        # Initialize handlers
        print("🔧 Setting up message handlers...")
        handlers = HandlerManager()
        
        # Add simple echo handler for testing basic functionality
        print("🔊 Adding test echo handler...")
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
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
        
        # Keep the application running (replacing the idle() method)
        try:
            # Simple loop to keep the program running
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            # On keyboard interrupt, stop the application
            await application.stop()
            await application.shutdown()
        
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