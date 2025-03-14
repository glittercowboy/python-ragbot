# handlers/base_handler.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import DatabaseService
from whisper_service import WhisperService
from claude_service import ClaudeService
from game_service import GameService

logger = logging.getLogger(__name__)

class BaseHandler:
    """Base class for all handlers with common functionality."""
    
    def __init__(self, db_service=None, whisper_service=None, 
                 claude_service=None, game_service=None):
        """Initialize with service instances or create new ones."""
        self.db_service = db_service or DatabaseService()
        self.whisper_service = whisper_service or WhisperService()
        self.claude_service = claude_service or ClaudeService()
        self.game_service = game_service or GameService(self.db_service, self.claude_service)
        
    def log_info(self, message):
        """Log info message."""
        logger.info(message)
        
    def log_error(self, message, error=None):
        """Log error message with optional exception."""
        if error:
            logger.error(f"{message}: {error}")
        else:
            logger.error(message)
            
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Base method to be overridden by subclasses."""
        # This is a placeholder method that should be overridden by subclasses
        logger.warning("BaseHandler.handle_message called directly - this should be overridden by a subclass")
        await update.message.reply_text("Sorry, this handler doesn't process messages.")