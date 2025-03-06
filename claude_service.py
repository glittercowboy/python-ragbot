# claude_service.py
import logging
import anthropic
import config
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        # You can change to a different Claude model
        self.model = "claude-3-7-sonnet-20250219"

    async def generate_response(self, user_query: str, context_entries: List[Dict[Any, Any]]) -> str:
        """
        Generate a response using Claude with RAG context.

        Args:
            user_query: The user's question
            context_entries: List of relevant context entries from the database

        Returns:
            str: Claude's response
        """
        try:
            # Extract text from context entries
            context_texts = []
            categories_mentioned = set()

            for entry in context_entries:
                entry_text = ""
                categories = []

                # Extract text
                if "document" in entry and "text" in entry["document"]:
                    entry_text = entry["document"]["text"]
                elif "text" in entry:
                    entry_text = entry["text"]
                elif "metadata" in entry and "text" in entry["metadata"]:
                    entry_text = entry["metadata"]["text"]

                # Extract categories if available
                if "metadata" in entry and "categories" in entry["metadata"]:
                    categories = entry["metadata"]["categories"]
                    categories_mentioned.update(categories)

                # Add category information to the context
                if categories:
                    formatted_entry = f"[Categories: {', '.join(categories)}] {entry_text}"
                else:
                    formatted_entry = entry_text

                if formatted_entry:
                    context_texts.append(formatted_entry)

            # Format context for Claude
            if context_texts:
                context_str = "\n\n".join(context_texts)

                # Add information about categories in the query if relevant
                category_awareness = ""
                if "work" in user_query.lower() or "health" in user_query.lower() or \
                   "relationship" in user_query.lower() or "purpose" in user_query.lower():
                    category_awareness = (
                        "Note that thoughts are categorized into: work, health, relationships, and purpose. "
                        "If the user is asking about a specific category, focus on entries from that category.")

                system_prompt = (
                    "You are a personal AI assistant that knows the user well based on their past thoughts and interactions. "
                    "You should answer questions thoughtfully based on what you know about them. "
                    "If asked about the user's preferences, personality, or habits, rely on the context provided to give accurate, "
                    "personalized responses. When you don't have enough information, acknowledge the limitations in your knowledge "
                    "rather than making assumptions. Be conversational, supportive, and insightful.\n\n"
                    f"{category_awareness}\n\n"
                    f"Context about the user:\n{context_str}\n\n"
                    "Remember to focus on the context above when answering questions about the user."
                )
            else:
                system_prompt = (
                    "You are a personal AI assistant. You don't have specific information about the user yet, "
                    "but you're here to help. Be conversational, supportive, and thoughtful in your responses.")

            # Generate response - removed the await since Anthropic's client is synchronous
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_query}
                ]
            )

            # Extract the text content
            response_text = response.content[0].text

            logger.info(f"Generated Claude response for query: {user_query[:50]}...")
            return response_text

        except Exception as e:
            logger.error(f"Error generating Claude response: {e}")
            return "I'm sorry, I encountered an error while processing your question. Please try again."

    async def generate_game_question(self) -> str:
        """
        Generate a question for the 'get to know you' game.

        Returns:
            str: A question for the user
        """
        try:
            system_prompt = (
                "You are generating questions for a 'get to know you' game. "
                "Create thoughtful, open-ended questions that help understand a person's values, "
                "perspectives, habits, preferences, and personality. "
                "Questions should be introspective and reveal meaningful insights about the person. "
                "Avoid basic questions like 'what's your favorite color?' and instead ask deeper questions "
                "that encourage reflection and thoughtful responses.")

            user_prompt = (
                "Generate a single insightful question for getting to know someone better. "
                "Focus on understanding how they think, what they value, and what shapes their worldview. "
                "Make it open-ended and introspective.")

            # Create a synchronous request - Anthropic's Python client doesn't support async natively
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract the question
            question = response.content[0].text.strip()

            logger.info(f"Generated game question: {question}")
            return question

        except Exception as e:
            logger.error(f"Error generating game question: {e}")
            # Fallback question
            return "What's something that you've changed your mind about recently, and why?"