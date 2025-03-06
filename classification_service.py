# classification_service.py
import logging
from claude_service import ClaudeService
import config

logger = logging.getLogger(__name__)

class ClassificationService:
    """Service for classifying text into predefined categories."""
    
    CATEGORIES = ["work", "health", "relationships", "purpose"]
    
    def __init__(self, claude_service=None):
        self.claude_service = claude_service or ClaudeService()
        
        # Category descriptions for better classification
        self.category_descriptions = {
            "work": "Professional and productive activities - career, business, education, or other meaningful work. Includes professional growth, accomplishments, financial stability, and skills development.",
            
            "health": "Physical and mental wellbeing. Taking care of your body through exercise, nutrition, and rest, as well as maintaining emotional and psychological wellness through stress management, mindfulness, and mental health care.",
            
            "relationships": "Human connections - family, friends, romantic partners, and community. The quality of these relationships, how you nurture them, your social support system, and ability to form and maintain meaningful bonds.",
            
            "purpose": "Sense of meaning and direction in life. Values, beliefs, personal growth, and the impact you want to have on the world. Understanding why you do what you do and feeling your life has significance."
        }
    
    async def classify_text(self, text):
        """
        Classify text into one or more categories.
        
        Args:
            text: The text to classify
            
        Returns:
            list: Categories the text belongs to
        """
        try:
            # Create a prompt for Claude to classify the text
            system_prompt = (
                "You are a classifier that categorizes personal thoughts and reflections into these categories:\n"
                "- Work: Professional activities, career, business, productivity, skills, financial matters\n"
                "- Health: Physical and mental wellbeing, exercise, nutrition, sleep, stress, mindfulness\n"
                "- Relationships: Connections with family, friends, partners, social interactions\n"
                "- Purpose: Meaning, values, beliefs, goals, personal growth, impact\n\n"
                "A text can belong to multiple categories if it touches on multiple domains. "
                "Analyze the content carefully and assign all relevant categories."
            )
            
            user_prompt = (
                f"Classify this text into one or more of these categories: work, health, relationships, purpose.\n\n"
                f"Text: \"{text}\"\n\n"
                f"Respond with just a comma-separated list of the applicable categories, like: category1, category2"
            )
            
            # Get classification from Claude
            response = await self.claude_service.client.messages.create(
                model=self.claude_service.model,
                max_tokens=50,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse the response to get categories
            categories_text = response.content[0].text.strip().lower()
            
            # Extract categories
            extracted_categories = []
            for category in self.CATEGORIES:
                if category in categories_text:
                    extracted_categories.append(category)
            
            logger.info(f"Classified text into categories: {extracted_categories}")
            return extracted_categories
            
        except Exception as e:
            logger.error(f"Error classifying text: {e}")
            return []  # Return empty list on errorx