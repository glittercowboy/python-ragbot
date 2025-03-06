# handlers/normal_handler.py
import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler
import config

logger = logging.getLogger(__name__)

# Import USER_STATE dictionary to be shared across handlers
from handlers import USER_STATE

class NormalHandler(BaseHandler):
    """Handles messages in normal mode (storing thoughts)."""
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle messages in normal mode (storing thoughts)."""
        user_id = update.effective_user.id
        message = update.message
        
        # Initialize classification service if not already done
        if not hasattr(self, 'classification_service'):
            from classification_service import ClassificationService
            self.classification_service = ClassificationService(self.claude_service)
        
        # Check if it's a voice message
        if message.voice:
            await message.reply_text("🎙️ I received your voice note. Transcribing...")
            
            # Download the voice file
            voice_file = await context.bot.get_file(message.voice.file_id)
            file_path = os.path.join(config.AUDIO_DIR, f"{message.voice.file_id}.ogg")
            await voice_file.download_to_drive(file_path)
            
            # Transcribe the voice note
            transcribed_text = await self.whisper_service.transcribe_voice_note(file_path)
            
            if not transcribed_text:
                await message.reply_text("Sorry, I couldn't transcribe your voice note. Please try again.")
                return
            
            # Classify the transcribed text
            categories = await self.classification_service.classify_text(transcribed_text)
            
            # Store the transcribed text with categories
            metadata = {
                "user_id": user_id,
                "source": "voice_note",
                "created_at": datetime.now().isoformat()
            }
            
            entry_id = await self.db_service.store_entry(
                collection_name=config.DB_COLLECTION_THOUGHTS,
                text=transcribed_text,
                metadata=metadata,
                categories=categories
            )
            
            # Prepare category information for the response
            category_info = ""
            if categories:
                category_info = f"\nCategories: {', '.join(categories)}"
            
            if entry_id:
                await message.reply_text(
                    f"✅ I've transcribed and stored your thought:{category_info}\n\n"
                    f"\"{transcribed_text}\"\n\n"
                    f"You can find it later using /list or chat with me about it using /chat."
                )
            else:
                await message.reply_text("Sorry, I couldn't store your thought. Please try again.")
            
        # Check if it's a text message
        elif message.text and not message.text.startswith('/'):
            # Classify the text
            categories = await self.classification_service.classify_text(message.text)
            
            # Store the text with categories
            metadata = {
                "user_id": user_id,
                "source": "text_message",
                "created_at": datetime.now().isoformat()
            }
            
            entry_id = await self.db_service.store_entry(
                collection_name=config.DB_COLLECTION_THOUGHTS,
                text=message.text,
                metadata=metadata,
                categories=categories
            )
            
            # Prepare category information for the response
            category_info = ""
            if categories:
                category_info = f"\nCategories: {', '.join(categories)}"
            
            if entry_id:
                await message.reply_text(
                    f"✅ I've stored your thought.{category_info} You can find it later using /list or chat with me about it using /chat."
                )
            else:
                await message.reply_text("Sorry, I couldn't store your thought. Please try again.")