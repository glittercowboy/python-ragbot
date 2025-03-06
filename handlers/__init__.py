# handlers/__init__.py
# User states
USER_STATE = {}
# Thoughts IDs by user for potential deletion
USER_THOUGHTS = {}

# State constants
STATE_NORMAL = "normal"
STATE_GAME = "game"
STATE_CHAT = "chat"
STATE_DELETE = "delete"

import logging
import sys
from telegram import Update
from telegram.ext import ContextTypes
from handlers.command_handler import CommandHandler
from handlers.normal_handler import NormalHandler
from handlers.chat_handler import ChatHandler
from handlers.game_handler import GameHandler
from handlers.callback_handler import CallbackHandler

logger = logging.getLogger(__name__)

class HandlerManager:
    """Main handler class that coordinates all the sub-handlers."""
    
    def __init__(self):
        """Initialize all handlers with the same service instances."""
        try:
            print("📦 Initializing services...")
            # Create service instances to be shared
            from database import DatabaseService
            from whisper_service import WhisperService
            from claude_service import ClaudeService
            from game_service import GameService
            
            print("🗄️ Setting up database service...")
            db_service = DatabaseService()
            
            print("🎙️ Setting up voice transcription service...")
            whisper_service = WhisperService()
            
            print("🧠 Setting up Claude AI service...")
            claude_service = ClaudeService()
            
            print("🎮 Setting up game service...")
            game_service = GameService(db_service, claude_service)
            
            # Initialize handlers with shared services
            print("🔄 Initializing command handler...")
            self.command_handler = CommandHandler(
                db_service, whisper_service, claude_service, game_service
            )
            
            print("📥 Initializing normal message handler...")
            self.normal_handler = NormalHandler(
                db_service, whisper_service, claude_service, game_service
            )
            
            print("💬 Initializing chat handler...")
            self.chat_handler = ChatHandler(
                db_service, whisper_service, claude_service, game_service
            )
            
            print("🎯 Initializing game handler...")
            self.game_handler = GameHandler(
                db_service, whisper_service, claude_service, game_service
            )
            
            print("🔄 Initializing callback handler...")
            self.callback_handler = CallbackHandler(
                db_service, whisper_service, claude_service, game_service
            )
            
            print("✅ All handlers initialized successfully!")
            
        except Exception as e:
            error_msg = f"Fatal error during handler initialization: {e}"
            print(f"\n❌ {error_msg}")
            logger.error(error_msg)
            print("\nThe application cannot continue. Please fix the error and restart.")
            sys.exit(1)
    
    # Command handlers
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"👋 Received /start command from user {update.effective_user.id}")
        await self.command_handler.start_command(update, context)
        print(f"✅ Processed /start command for user {update.effective_user.id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"❓ Received /help command from user {update.effective_user.id}")
        await self.command_handler.help_command(update, context)
        print(f"✅ Processed /help command for user {update.effective_user.id}")
    
    async def chat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"💬 Received /chat command from user {update.effective_user.id}")
        await self.command_handler.chat_command(update, context)
        print(f"✅ Processed /chat command for user {update.effective_user.id}")
    
    async def game_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"🎮 Received /game command from user {update.effective_user.id}")
        await self.command_handler.game_command(update, context)
        print(f"✅ Processed /game command for user {update.effective_user.id}")
    
    async def normal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"🔄 Received /normal command from user {update.effective_user.id}")
        await self.command_handler.normal_command(update, context)
        print(f"✅ Processed /normal command for user {update.effective_user.id}")
    
    async def delete_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"🗑️ Received /delete command from user {update.effective_user.id}")
        await self.command_handler.delete_command(update, context)
        print(f"✅ Processed /delete command for user {update.effective_user.id}")
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"📋 Received /list command from user {update.effective_user.id}")
        await self.command_handler.list_command(update, context)
        print(f"✅ Processed /list command for user {update.effective_user.id}")
    
    async def category_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"🏷️ Received /category command from user {update.effective_user.id}")
        await self.command_handler.category_command(update, context)
        print(f"✅ Processed /category command for user {update.effective_user.id}")
    
    # Message handler
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Main message handler that delegates to specific handlers based on state."""
        user_id = update.effective_user.id
        
        # Debug message reception
        print(f"📨 Received message from user {user_id}: {update.message.text if update.message.text else '[Not text]'}")
        logger.info(f"Received message from user {user_id}: {update.message.text if update.message.text else '[Not text]'}")
        
        # Initialize state if not set
        if user_id not in USER_STATE:
            USER_STATE[user_id] = STATE_NORMAL
            print(f"🆕 Initialized state for user {user_id} to {STATE_NORMAL}")
        
        state = USER_STATE[user_id]
        print(f"🔄 Current state for user {user_id}: {state}")
        
        try:
            if state == STATE_NORMAL:
                print(f"📝 Delegating to normal handler for user {user_id}")
                await self.normal_handler.handle_message(update, context)
                print(f"✅ Normal handler processed message for user {user_id}")
            elif state == STATE_CHAT:
                print(f"💬 Delegating to chat handler for user {user_id}")
                await self.chat_handler.handle_message(update, context)
                print(f"✅ Chat handler processed message for user {user_id}")
            elif state == STATE_GAME:
                print(f"🎮 Delegating to game handler for user {user_id}")
                await self.game_handler.handle_message(update, context)
                print(f"✅ Game handler processed message for user {user_id}")
            elif state == STATE_DELETE:
                # Should be handled by the callback query handler
                print(f"❌ User {user_id} is in delete mode, sending instruction")
                await update.message.reply_text(
                    "Please use the buttons to select a thought to delete, or type /normal to cancel."
                )
                print(f"✅ Sent delete mode instructions to user {user_id}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            print(f"❌ Error handling message for user {user_id}: {e}")
            await update.message.reply_text(
                "Sorry, I encountered an error processing your message. Please try again."
            )
    
    # Callback query handler
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.callback_query.from_user.id
        print(f"🔄 Received callback query from user {user_id}: {update.callback_query.data}")
        await self.callback_handler.handle_callback_query(update, context)
        print(f"✅ Processed callback query for user {user_id}")