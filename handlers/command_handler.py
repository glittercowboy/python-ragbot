# handlers/command_handler.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler
import config

logger = logging.getLogger(__name__)

# Import USER_STATE dictionary to be shared across handlers
from handlers import USER_STATE, USER_THOUGHTS
from handlers import STATE_NORMAL, STATE_CHAT, STATE_GAME, STATE_DELETE

class CommandHandler(BaseHandler):
    """Handles all bot commands."""
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a welcome message when the command /start is issued."""
        user_id = update.effective_user.id
        USER_STATE[user_id] = STATE_NORMAL
        
        welcome_text = (
            "👋 Welcome to your Personal Reflection Bot!\n\n"
            "I'm here to help you store thoughts, answer questions about yourself, "
            "and learn more about you through interactive games.\n\n"
            "Here's what you can do:\n"
            "• Send me text or voice notes to store your thoughts\n"
            "• Use /chat to ask questions about yourself based on your stored thoughts\n"
            "• Use /game to play a 'get to know you' game\n"
            "• Use /delete to remove stored thoughts\n"
            "• Use /category to view thoughts by category\n"
            "• Use /help to see all commands\n\n"
            "Let's get started! How can I help you today?"
        )
        
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a help message when the command /help is issued."""
        help_text = (
            "🤖 **Personal Reflection Bot Help**\n\n"
            "**Basic Commands:**\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n\n"
            
            "**Modes:**\n"
            "/chat - Enter chat mode to ask questions\n"
            "/game - Start a 'get to know you' game\n"
            "/normal - Return to normal mode for storing thoughts\n\n"
            
            "**Other Commands:**\n"
            "/delete - List thoughts you can delete\n"
            "/list - List your recent thoughts\n"
            "/category - View thoughts by category (work, health, relationships, purpose)\n\n"
            
            "**How to use:**\n"
            "• In normal mode: Send text or voice messages to store your thoughts\n"
            "• In chat mode: Ask me questions about yourself\n"
            "• In game mode: Answer the questions I ask you\n\n"
            
            "I'm here to help you reflect on your thoughts and learn more about yourself!"
        )
        
        await update.message.reply_text(help_text)
    
    async def chat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Switch to chat mode."""
        user_id = update.effective_user.id
        USER_STATE[user_id] = STATE_CHAT
        
        await update.message.reply_text(
            "📝 You're now in chat mode. Ask me anything, and I'll use your stored thoughts to answer!"
        )
    
    async def game_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Start the 'get to know you' game."""
        user_id = update.effective_user.id
        USER_STATE[user_id] = STATE_GAME
        
        # Get the first question
        question = await self.game_service.start_game(user_id)
        
        await update.message.reply_text(
            f"🎮 Let's play a 'get to know you' game! I'll ask questions to learn more about you.\n\n"
            f"First question: {question}\n\n"
            f"(Reply with text or send a voice note with your answer)"
        )
    
    async def normal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Switch to normal mode for storing thoughts."""
        user_id = update.effective_user.id
        USER_STATE[user_id] = STATE_NORMAL
        
        await update.message.reply_text(
            "🔄 You're now in normal mode. Send me your thoughts as text or voice notes, and I'll store them for you."
        )
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """List recent thoughts."""
        user_id = update.effective_user.id
        
        # Get recent thoughts
        thoughts = await self.db_service.get_all_entries(
            collection_name=config.DB_COLLECTION_THOUGHTS,
            page=1,
            page_size=10
        )
        
        if not thoughts:
            await update.message.reply_text("You don't have any stored thoughts yet.")
            return
        
        # Create a list of thoughts
        thought_list = "Your recent thoughts:\n\n"
        for i, thought in enumerate(thoughts, 1):
            text = thought.get("text", "")
            if "metadata" in thought and "text" in thought["metadata"]:
                text = thought["metadata"]["text"]
            
            # Truncate long thoughts
            if len(text) > 100:
                text = text[:100] + "..."
            
            # Add timestamp if available
            timestamp = ""
            if "metadata" in thought and "created_at" in thought["metadata"]:
                timestamp = f" ({thought['metadata']['created_at'][:10]})"
            
            # Add categories if available
            categories = ""
            if "metadata" in thought and "categories" in thought["metadata"]:
                categories = f" [{', '.join(thought['metadata']['categories'])}]"
            
            thought_list += f"{i}.{timestamp}{categories} {text}\n\n"
        
        await update.message.reply_text(thought_list)
    
    async def delete_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show thoughts that can be deleted."""
        user_id = update.effective_user.id
        USER_STATE[user_id] = STATE_DELETE
        
        # Get recent thoughts
        thoughts = await self.db_service.get_all_entries(
            collection_name=config.DB_COLLECTION_THOUGHTS,
            page=1,
            page_size=10
        )
        
        if not thoughts:
            await update.message.reply_text("You don't have any stored thoughts yet.")
            USER_STATE[user_id] = STATE_NORMAL
            return
        
        # Store thoughts with their IDs for this user
        USER_THOUGHTS[user_id] = {i+1: thought for i, thought in enumerate(thoughts)}
        
        # Create a list of thoughts with numbers
        thought_list = "Select a thought to delete:\n\n"
        for i, thought in enumerate(thoughts, 1):
            text = thought.get("text", "")
            if "metadata" in thought and "text" in thought["metadata"]:
                text = thought["metadata"]["text"]
            
            # Truncate long thoughts
            if len(text) > 100:
                text = text[:100] + "..."
            
            # Add categories if available
            categories = ""
            if "metadata" in thought and "categories" in thought["metadata"]:
                categories = f" [{', '.join(thought['metadata']['categories'])}]"
            
            thought_list += f"{i}.{categories} {text}\n\n"
        
        # Create inline keyboard
        keyboard = []
        row = []
        for i in range(1, len(thoughts) + 1):
            if len(row) == 3:  # 3 buttons per row
                keyboard.append(row)
                row = []
            row.append(InlineKeyboardButton(str(i), callback_data=f"delete_{i}"))
        
        if row:  # Add any remaining buttons
            keyboard.append(row)
        
        # Add cancel button
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="delete_cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(thought_list, reply_markup=reply_markup)
    
    async def category_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show thoughts by category."""
        # Check if category was provided
        if not context.args or len(context.args) < 1:
            categories = ["work", "health", "relationships", "purpose"]
            await update.message.reply_text(
                "Please specify a category:\n"
                "/category work - work-related thoughts\n"
                "/category health - health-related thoughts\n"
                "/category relationships - relationship-related thoughts\n"
                "/category purpose - purpose-related thoughts"
            )
            return
        
        category = context.args[0].lower()
        valid_categories = ["work", "health", "relationships", "purpose"]
        
        if category not in valid_categories:
            await update.message.reply_text(
                f"'{category}' is not a valid category. Please use one of: {', '.join(valid_categories)}"
            )
            return
        
        # Search for thoughts in the specified category
        thoughts = await self.db_service.search_by_category(
            collection_name=config.DB_COLLECTION_THOUGHTS,
            category=category,
            limit=10
        )
        
        if not thoughts:
            await update.message.reply_text(f"You don't have any thoughts categorized as '{category}' yet.")
            return
        
        # Create a list of thoughts
        thought_list = f"Your thoughts related to {category}:\n\n"
        for i, thought in enumerate(thoughts, 1):
            text = thought.get("text", "")
            if "metadata" in thought and "text" in thought["metadata"]:
                text = thought["metadata"]["text"]
            
            # Truncate long thoughts
            if len(text) > 100:
                text = text[:100] + "..."
            
            # Add timestamp if available
            timestamp = ""
            if "metadata" in thought and "created_at" in thought["metadata"]:
                timestamp = f" ({thought['metadata']['created_at'][:10]})"
            
            thought_list += f"{i}.{timestamp} {text}\n\n"
        
        await update.message.reply_text(thought_list)