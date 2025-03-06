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
                logger.info(f"Processing deletion for thought index {thought_index}")
                
                if user_id not in USER_THOUGHTS:
                    logger.error(f"User {user_id} not found in USER_THOUGHTS")
                    await query.edit_message_text("Error: User data not found. Please try again.")
                    USER_STATE[user_id] = STATE_NORMAL
                    return
                
                if thought_index not in USER_THOUGHTS[user_id]:
                    logger.error(f"Thought index {thought_index} not found for user {user_id}")
                    await query.edit_message_text("Error: Thought not found. Please try again.")
                    USER_STATE[user_id] = STATE_NORMAL
                    return
                
                thought = USER_THOUGHTS[user_id][thought_index]
                logger.info(f"Found thought for deletion: {thought}")
                
                # Extract thought_id safely with better logging
                thought_id = None
                if isinstance(thought, dict):
                    logger.info(f"Thought keys: {thought.keys()}")
                    if "_id" in thought:
                        thought_id = thought["_id"]
                        logger.info(f"Found thought ID: {thought_id}")
                    else:
                        logger.error(f"No _id key found in thought")
                else:
                    logger.error(f"Thought is not a dict: {type(thought)}")
                
                if not thought_id:
                    # Try harder to find the ID by dumping the whole thought
                    logger.info(f"Thought content dump: {thought}")
                    await query.edit_message_text("Could not find the thought ID. Please try again.")
                    USER_STATE[user_id] = STATE_NORMAL
                    return
                
                # Delete the thought
                logger.info(f"Attempting to delete thought with ID: {thought_id}")
                success = await self.db_service.delete_entry(
                    collection_name=config.DB_COLLECTION_THOUGHTS,
                    entry_id=thought_id
                )
                
                if success:
                    await query.edit_message_text("✅ Thought deleted successfully.")
                    logger.info(f"Successfully deleted thought with ID: {thought_id}")
                else:
                    await query.edit_message_text("❌ Failed to delete the thought. Please try again.")
                    logger.error(f"Failed to delete thought with ID: {thought_id}")
                
                # Clean up and reset state
                if user_id in USER_THOUGHTS:
                    del USER_THOUGHTS[user_id]
                USER_STATE[user_id] = STATE_NORMAL
                
            except (ValueError, KeyError) as e:
                logger.error(f"Error deleting thought: {e}")
                await query.edit_message_text("An error occurred while deleting the thought.")
                USER_STATE[user_id] = STATE_NORMAL