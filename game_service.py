# game_service.py
import logging
import random
from database import DatabaseService
from claude_service import ClaudeService
import config

logger = logging.getLogger(__name__)

class GameService:
    def __init__(self, db_service: DatabaseService, claude_service: ClaudeService):
        self.db_service = db_service
        self.claude_service = claude_service
        self.active_games = {}  # Track active games by user_id
        
        # List of diverse fallback questions in case Claude API fails
        self.fallback_questions = [
            "What's something that you've changed your mind about recently, and why?",
            "What personal quality do you appreciate most in yourself?",
            "What's a skill you'd love to master in the next few years?",
            "What's a small moment from your life that had a big impact on who you are today?",
            "What's a belief you hold that most people disagree with?",
            "What's something you wish more people understood about you?",
            "If you could give advice to your younger self, what would it be?",
            "What's a challenge you've faced that ended up being valuable?",
            "What's something you're curious about but haven't explored yet?",
            "What's a compliment someone gave you that you particularly value?",
            "What values or principles guide your decisions?",
            "What's a meaningful goal you're working toward right now?",
            "What's a question you've been asking yourself lately?",
            "What makes you feel most alive or energized?",
            "What's a meaningful connection or relationship in your life?"
        ]
    
    async def start_game(self, user_id: int) -> str:
        """
        Start a new 'get to know you' game for a user.
        
        Args:
            user_id: The Telegram user ID
            
        Returns:
            str: The first question
        """
        try:
            # Generate a question
            question = await self.claude_service.generate_game_question()
            
            # Save the active game state
            self.active_games[user_id] = {
                "current_question": question,
                "question_count": 1,
                "asked_questions": [question]  # Track questions we've asked
            }
            
            return question
            
        except Exception as e:
            logger.error(f"Error starting game for user {user_id}: {e}")
            # Get a random fallback question
            fallback = random.choice(self.fallback_questions)
            
            # Initialize game state with fallback
            self.active_games[user_id] = {
                "current_question": fallback,
                "question_count": 1,
                "asked_questions": [fallback]
            }
            
            return fallback
    
    async def handle_answer(self, user_id: int, answer_text: str) -> str:
        """
        Process a user's answer to a game question and provide the next question.
        
        Args:
            user_id: The Telegram user ID
            answer_text: The user's answer to the current question
            
        Returns:
            str: The next question or a game end message
        """
        try:
            # Check if there's an active game for this user
            if user_id not in self.active_games:
                return await self.start_game(user_id)
            
            game_state = self.active_games[user_id]
            current_question = game_state["current_question"]
            
            # Store the answer with its question
            metadata = {
                "question": current_question,
                "question_number": game_state["question_count"],
                "user_id": user_id
            }
            
            await self.db_service.store_entry(
                collection_name=config.DB_COLLECTION_GAME,
                text=answer_text,
                metadata=metadata
            )
            
            # Decide whether to continue the game or end it
            game_state["question_count"] += 1
            
            if game_state["question_count"] > 5:  # Limit to 5 questions per session
                # End the game
                del self.active_games[user_id]
                return "Thank you for sharing! I've learned a lot about you. You can start a new game anytime."
            
            # Generate the next question
            attempts = 0
            max_attempts = 3
            next_question = ""
            
            # Try to get a unique question that hasn't been asked before
            while attempts < max_attempts:
                next_question = await self.claude_service.generate_game_question()
                
                # Check if we've asked this or very similar question before
                if next_question not in game_state["asked_questions"]:
                    # Check for similarity with previous questions (this is simplified,
                    # but you could use more sophisticated text similarity methods)
                    similar = False
                    for asked in game_state["asked_questions"]:
                        # Very basic similarity check - could be improved
                        if len(set(next_question.split()) & set(asked.split())) > 5:
                            similar = True
                            break
                    
                    if not similar:
                        break
                
                attempts += 1
            
            # If we couldn't get a unique question after max attempts,
            # use a fallback question that hasn't been asked yet
            if attempts >= max_attempts or not next_question:
                available_fallbacks = [q for q in self.fallback_questions 
                                     if q not in game_state["asked_questions"]]
                
                if available_fallbacks:
                    next_question = random.choice(available_fallbacks)
                else:
                    # If we've exhausted all fallbacks too, use any fallback
                    next_question = random.choice(self.fallback_questions)
            
            # Update game state
            game_state["current_question"] = next_question
            game_state["asked_questions"].append(next_question)
            
            return next_question
            
        except Exception as e:
            logger.error(f"Error handling game answer for user {user_id}: {e}")
            # Get a fallback question not yet asked in this game
            if user_id in self.active_games and "asked_questions" in self.active_games[user_id]:
                asked = self.active_games[user_id]["asked_questions"]
                available = [q for q in self.fallback_questions if q not in asked]
                if available:
                    return random.choice(available)
            
            return random.choice(self.fallback_questions)