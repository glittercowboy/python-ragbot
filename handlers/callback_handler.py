# handlers/callback_handler.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)

# Import USER_STATE dictionary to be shared across handlers
from handlers import USER_STATE, USER_THOUGHTS, STATE_NORMAL

class CallbackHandler(BaseHandler):
    """Handles callback queries from inline keyboards."""
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data.startswith("delete_"):
            thought_num = data.replace("delete_", "")
            
            if thought_num == "cancel":
                USER_STATE[user_id] = STATE_NORMAL
                await query.edit_message_text("Deletion canceled. You're back in normal mode.")
                return
            
            # Get the thought to delete
            try:
                thought_index = int(thought_num)
                if user_id not in USER_THOUGHTS or thought_index not in USER_THOUGHTS[user_id]:
                    await query.edit_message_text("This thought is no longer available.")
                    USER_STATE[user_id] = STATE_NORMAL
                    return
                
                thought = USER_THOUGHTS[user_id][thought_index]
                
                # Extract thought_id safely
                thought_id = None
                if isinstance(thought, dict) and "_id" in thought:
                    thought_id = thought["_id"]
                
                if not thought_id:
                    await query.edit_message_text("Could not find the thought ID. Please try again.")
                    USER_STATE[user_id] = STATE_NORMAL
                    return
                
                # Delete the thought
                success = await self.db_service.delete_entry(
                    collection_name=config.DB_COLLECTION_THOUGHTS,
                    entry_id=thought_id
                )
                
                if success:
                    await query.edit_message_text("✅ Thought deleted successfully.")
                else:
                    await query.edit_message_text("❌ Failed to delete the thought. Please try again.")
                
                # Clean up and reset state
                if user_id in USER_THOUGHTS:
                    del USER_THOUGHTS[user_id]
                USER_STATE[user_id] = STATE_NORMAL
                
            except (ValueError, KeyError) as e:
                logger.error(f"Error deleting thought: {e}")
                await query.edit_message_text("An error occurred while deleting the thought.")
                USER_STATE[user_id] = STATE_NORMAL