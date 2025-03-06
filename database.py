# database.py
import uuid
import logging
import datetime
from astrapy.db import AstraDB, AstraDBCollection
from astrapy.ops import AstraDBOps
import config

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        try:
            # Initialize connection to AstraDB
            self.db = AstraDB(
                token=config.ASTRA_DB_APPLICATION_TOKEN,
                api_endpoint=config.ASTRA_DB_API_ENDPOINT
            )
            
            # Initialize collections
            self.thoughts_collection = self._get_or_create_collection(config.DB_COLLECTION_THOUGHTS)
            self.game_collection = self._get_or_create_collection(config.DB_COLLECTION_GAME)
            self.chat_collection = self._get_or_create_collection(config.DB_COLLECTION_CHAT)
            
            logger.info("Successfully connected to AstraDB")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise

    def _get_or_create_collection(self, collection_name):
        """Get or create a collection with the given name."""
        try:
            # Check if collection exists
            collections = self.db.get_collections()
            if collection_name not in [c["name"] for c in collections["status"]["collections"]]:
                # Create collection if it doesn't exist
                self.db.create_collection(
                    collection_name=collection_name,
                    dimension=1536  # Default dimension for OpenAI embeddings
                )
                logger.info(f"Created new collection: {collection_name}")
            
            # Get the collection
            return AstraDBCollection(
                collection_name=collection_name,
                astra_db=self.db
            )
        except Exception as e:
            logger.error(f"Error getting/creating collection {collection_name}: {e}")
            raise

    async def store_entry(self, collection_name, text, metadata=None, categories=None):
        """Store text as a vector embedding with metadata and categories."""
        try:
            if not text:
                logger.warning("Attempted to store empty text")
                return None
                
            collection = self._get_collection_by_name(collection_name)
            
            # Generate a unique ID
            entry_id = str(uuid.uuid4())
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            metadata["text"] = text
            metadata["created_at"] = str(datetime.datetime.now())
            
            # Add categories if provided
            if categories:
                metadata["categories"] = categories
            
            # Store the document with its vector embedding
            # Note: AstraDB will handle the embedding generation automatically with Astra Vectorize
            result = await collection.insert_one({
                "_id": entry_id,
                "text": text,
                "metadata": metadata
            })
            
            logger.info(f"Stored entry in {collection_name} with ID: {entry_id}")
            return entry_id
            
        except Exception as e:
            logger.error(f"Error storing entry in {collection_name}: {e}")
            return None

    async def search_similar(self, collection_name, query_text, limit=5):
        """Search for similar entries using vector similarity."""
        try:
            collection = self._get_collection_by_name(collection_name)
            
            results = await collection.vector_find(
                query_text,
                limit=limit
            )
            
            logger.info(f"Found {len(results)} similar entries in {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching in {collection_name}: {e}")
            return []

    async def search_by_category(self, collection_name, category, limit=10):
        """Search for entries in a specific category."""
        try:
            collection = self._get_collection_by_name(collection_name)
            
            results = await collection.find(
                filter={"metadata.categories": {"$in": [category]}},
                options={"limit": limit}
            )
            
            logger.info(f"Found {len(results)} entries in category '{category}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching category '{category}' in {collection_name}: {e}")
            return []

    async def delete_entry(self, collection_name, entry_id):
        """Delete an entry by ID."""
        try:
            collection = self._get_collection_by_name(collection_name)
            
            result = await collection.delete_one({"_id": entry_id})
            
            if result and result.get("deletedCount", 0) > 0:
                logger.info(f"Deleted entry {entry_id} from {collection_name}")
                return True
            else:
                logger.warning(f"Entry {entry_id} not found in {collection_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting entry {entry_id} from {collection_name}: {e}")
            return False

    def _get_collection_by_name(self, collection_name):
        """Get the appropriate collection based on the name."""
        if collection_name == config.DB_COLLECTION_THOUGHTS:
            return self.thoughts_collection
        elif collection_name == config.DB_COLLECTION_GAME:
            return self.game_collection
        elif collection_name == config.DB_COLLECTION_CHAT:
            return self.chat_collection
        else:
            raise ValueError(f"Unknown collection name: {collection_name}")

    async def get_all_entries(self, collection_name, page=1, page_size=10):
        """Get all entries from a collection with pagination."""
        try:
            collection = self._get_collection_by_name(collection_name)
            
            # Calculate skip amount for pagination
            skip = (page - 1) * page_size
            
            # Find documents
            results = await collection.find(
                filter={},
                options={"limit": page_size, "skip": skip}
            )
            
            logger.info(f"Retrieved {len(results)} entries from {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving entries from {collection_name}: {e}")
            return []