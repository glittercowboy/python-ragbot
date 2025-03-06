# handlers/game_handler.py
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler
import config

logger = logging.getLogger(__name__)

# Import USER_STATE dictionary to be shared across handlers
from handlers import USER_STATE, STATE_NORMAL

class GameHandler(BaseHandler):
    """Handles messages in game mode."""
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle messages in game mode."""
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
            answer_text = await self.whisper_service.transcribe_voice_note(file_path)
            
            if not answer_text:
                await message.reply_text("Sorry, I couldn't transcribe your voice note. Please try again.")
                return
            
            await message.reply_text(f"I understood your answer as: \"{answer_text}\"")
        
        # Handle text message
        elif message.text and not message.text.startswith('/'):
            answer_text = message.text
        else:
            return
        
        # Process the answer and get the next question
        next_question = await self.game_service.handle_answer(user_id, answer_text)
        
        # Check if the game has ended
        if "Thank you for sharing!" in next_question:
            USER_STATE[user_id] = STATE_NORMAL
            await message.reply_text(next_question)
        else:
            await message.reply_text(f"Next question: {next_question}")