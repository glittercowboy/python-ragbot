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
        await self.command_handler.start_command(update, context)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.command_handler.help_command(update, context)
    
    async def chat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.command_handler.chat_command(update, context)
    
    async def game_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.command_handler.game_command(update, context)
    
    async def normal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.command_handler.normal_command(update, context)
    
    async def delete_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.command_handler.delete_command(update, context)
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.command_handler.list_command(update, context)
    
    async def category_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.command_handler.category_command(update, context)
    
    # Message handler
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Main message handler that delegates to specific handlers based on state."""
        user_id = update.effective_user.id
        
        # Initialize state if not set
        if user_id not in USER_STATE:
            USER_STATE[user_id] = STATE_NORMAL
        
        state = USER_STATE[user_id]
        
        try:
            if state == STATE_NORMAL:
                await self.normal_handler.handle_message(update, context)
            elif state == STATE_CHAT:
                await self.chat_handler.handle_message(update, context)
            elif state == STATE_GAME:
                await self.game_handler.handle_message(update, context)
            elif state == STATE_DELETE:
                # Should be handled by the callback query handler
                await update.message.reply_text(
                    "Please use the buttons to select a thought to delete, or type /normal to cancel."
                )
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "Sorry, I encountered an error processing your message. Please try again."
            )
    
    # Callback query handler
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.callback_handler.handle_callback_query(update, context)