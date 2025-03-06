# handlers/chat_handler.py
import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler
import config

logger = logging.getLogger(__name__)

class ChatHandler(BaseHandler):
    """Handles messages in chat mode (answering questions)."""
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle messages in chat mode (answering questions)."""
        user_id = update.effective_user.id
        message = update.message
        
        # Handle voice message
        if message.voice:
            await message.reply_text("🎙️ I received your voice note. Transcribing...")
            
            # Download the voice file
            voice_file = await context.bot.get_file(message.voice.file_id)
            file_path = os.path.join(config.AUDIO_DIR, f"{message.voice.file_id}.ogg")
            await voice_file.download_to_drive(file_path)
            
            # Transcribe the voice note
            query_text = await self.whisper_service.transcribe_voice_note(file_path)
            
            if not query_text:
                await message.reply_text("Sorry, I couldn't transcribe your voice note. Please try again.")
                return
            
            await message.reply_text(f"I understood your question as: \"{query_text}\"")
        
        # Handle text message
        elif message.text and not message.text.startswith('/'):
            query_text = message.text
        else:
            return
        
        # Store the interaction
        metadata = {
            "user_id": user_id,
            "source": "chat_interaction",
            "created_at": datetime.now().isoformat()
        }
        
        await self.db_service.store_entry(
            collection_name=config.DB_COLLECTION_CHAT,
            text=query_text,
            metadata=metadata
        )
        
        # Search for relevant context
        await message.reply_text("🔍 Let me think about that...")
        
        # Collect context from all collections
        thoughts_context = await self.db_service.search_similar(
            collection_name=config.DB_COLLECTION_THOUGHTS,
            query_text=query_text,
            limit=3
        )
        
        game_context = await self.db_service.search_similar(
            collection_name=config.DB_COLLECTION_GAME,
            query_text=query_text,
            limit=3
        )
        
        chat_context = await self.db_service.search_similar(
            collection_name=config.DB_COLLECTION_CHAT,
            query_text=query_text,
            limit=3
        )
        
        # Combine all contexts
        all_context = thoughts_context + game_context + chat_context
        
        # Generate a response using Claude
        response = await self.claude_service.generate_response(
            user_query=query_text,
            context_entries=all_context
        )
        
        await message.reply_text(response)