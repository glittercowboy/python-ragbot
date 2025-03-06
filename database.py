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
            
            print("🔌 Connecting to database...")
            # Initialize collections
            self.thoughts_collection = self._get_or_create_collection(config.DB_COLLECTION_THOUGHTS)
            print(f"✅ Created/accessed collection: {config.DB_COLLECTION_THOUGHTS}")
            
            self.game_collection = self._get_or_create_collection(config.DB_COLLECTION_GAME)
            print(f"✅ Created/accessed collection: {config.DB_COLLECTION_GAME}")
            
            self.chat_collection = self._get_or_create_collection(config.DB_COLLECTION_CHAT)
            print(f"✅ Created/accessed collection: {config.DB_COLLECTION_CHAT}")
            
            logger.info("Successfully connected to AstraDB")
            print("🎉 Successfully connected to database!")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            print(f"❌ Database connection failed: {e}")
            raise

    def _get_or_create_collection(self, collection_name):
        """Get or create a collection with the given name."""
        try:
            # Check if collection exists
            print(f"🔍 Checking if collection '{collection_name}' exists...")
            collections_response = self.db.get_collections()
            
            # Improved error handling and logging for debugging
            if not isinstance(collections_response, dict):
                print(f"⚠️ Unexpected response type from get_collections(): {type(collections_response)}")
                logger.warning(f"Unexpected response type from get_collections(): {type(collections_response)}")
                print(f"Response content: {collections_response}")
                
            if "status" not in collections_response:
                print(f"⚠️ 'status' key missing in collections response: {collections_response}")
                logger.warning(f"'status' key missing in collections response: {collections_response}")
                # Fall back to creating the collection anyway
                self.db.create_collection(
                    collection_name=collection_name,
                    dimension=1536  # Default dimension for OpenAI embeddings
                )
                print(f"🆕 Created new collection: {collection_name}")
                logger.info(f"Created new collection: {collection_name}")
            else:
                collection_names = [c["name"] for c in collections_response["status"]["collections"]]
                
                if collection_name not in collection_names:
                    # Create collection if it doesn't exist
                    print(f"🆕 Creating new collection: {collection_name}")
                    self.db.create_collection(
                        collection_name=collection_name,
                        dimension=1536  # Default dimension for OpenAI embeddings
                    )
                    print(f"✅ Created new collection: {collection_name}")
                    logger.info(f"Created new collection: {collection_name}")
                else:
                    print(f"✅ Collection '{collection_name}' already exists")
            
            # Get the collection
            collection = AstraDBCollection(
                collection_name=collection_name,
                astra_db=self.db
            )
            return collection
            
        except Exception as e:
            error_msg = f"Error getting/creating collection {collection_name}: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise

    async def store_entry(self, collection_name, text, metadata=None, categories=None):
        """Store text as a vector embedding with metadata and categories."""
        try:
            if not text:
                logger.warning("Attempted to store empty text")
                print("⚠️ Attempted to store empty text")
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
            print(f"💾 Storing entry in {collection_name}...")
            # Note: AstraDB will handle the embedding generation automatically with Astra Vectorize
            result = await collection.insert_one({
                "_id": entry_id,
                "text": text,
                "metadata": metadata
            })
            
            print(f"✅ Stored entry in {collection_name} with ID: {entry_id}")
            logger.info(f"Stored entry in {collection_name} with ID: {entry_id}")
            return entry_id
            
        except Exception as e:
            error_msg = f"Error storing entry in {collection_name}: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            return None

    async def search_similar(self, collection_name, query_text, limit=5):
        """Search for similar entries using vector similarity."""
        try:
            collection = self._get_collection_by_name(collection_name)
            
            print(f"🔍 Searching for similar entries in {collection_name}...")
            results = await collection.vector_find(
                query_text,
                limit=limit
            )
            
            print(f"✅ Found {len(results)} similar entries in {collection_name}")
            logger.info(f"Found {len(results)} similar entries in {collection_name}")
            return results
            
        except Exception as e:
            error_msg = f"Error searching in {collection_name}: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            return []

    async def search_by_category(self, collection_name, category, limit=10):
        """Search for entries in a specific category."""
        try:
            collection = self._get_collection_by_name(collection_name)
            
            print(f"🔍 Searching for entries in category '{category}'...")
            results = await collection.find(
                filter={"metadata.categories": {"$in": [category]}},
                options={"limit": limit}
            )
            
            print(f"✅ Found {len(results)} entries in category '{category}'")
            logger.info(f"Found {len(results)} entries in category '{category}'")
            return results
            
        except Exception as e:
            error_msg = f"Error searching category '{category}' in {collection_name}: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            return []

    async def delete_entry(self, collection_name, entry_id):
        """Delete an entry by ID."""
        try:
            collection = self._get_collection_by_name(collection_name)
            
            print(f"🗑️ Deleting entry {entry_id} from {collection_name}...")
            result = await collection.delete_one({"_id": entry_id})
            
            if result and result.get("deletedCount", 0) > 0:
                print(f"✅ Deleted entry {entry_id} from {collection_name}")
                logger.info(f"Deleted entry {entry_id} from {collection_name}")
                return True
            else:
                print(f"⚠️ Entry {entry_id} not found in {collection_name}")
                logger.warning(f"Entry {entry_id} not found in {collection_name}")
                return False
                
        except Exception as e:
            error_msg = f"Error deleting entry {entry_id} from {collection_name}: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
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
            error_msg = f"Unknown collection name: {collection_name}"
            print(f"❌ {error_msg}")
            raise ValueError(error_msg)

    async def get_all_entries(self, collection_name, page=1, page_size=10):
        """Get all entries from a collection with pagination."""
        try:
            collection = self._get_collection_by_name(collection_name)
            
            # Calculate skip amount for pagination
            skip = (page - 1) * page_size
            
            print(f"📋 Retrieving entries from {collection_name} (page {page}, size {page_size})...")
            # Find documents
            results = await collection.find(
                filter={},
                options={"limit": page_size, "skip": skip}
            )
            
            print(f"✅ Retrieved {len(results)} entries from {collection_name}")
            logger.info(f"Retrieved {len(results)} entries from {collection_name}")
            return results
            
        except Exception as e:
            error_msg = f"Error retrieving entries from {collection_name}: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            return []