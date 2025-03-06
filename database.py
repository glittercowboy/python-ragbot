# database.py
import uuid
import logging
import datetime
import json
from astrapy.db import AstraDB, AstraDBCollection
import config

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        """Initialize the database service with connection to AstraDB."""
        try:
            print("🔌 Connecting to AstraDB...")
            self.db = AstraDB(
                token=config.ASTRA_DB_APPLICATION_TOKEN,
                api_endpoint=config.ASTRA_DB_API_ENDPOINT
            )
            
            print("✅ Connected to AstraDB successfully")
            
            # Initialize collections
            self._init_collections()
            
        except Exception as e:
            error_msg = f"Failed to initialize database connection: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise

    def _init_collections(self):
        """Initialize all required collections."""
        try:
            print("🏗️ Setting up collections...")
            
            # Create each collection with better error handling
            self.thoughts_collection = self._safely_create_collection(config.DB_COLLECTION_THOUGHTS)
            self.game_collection = self._safely_create_collection(config.DB_COLLECTION_GAME)
            self.chat_collection = self._safely_create_collection(config.DB_COLLECTION_CHAT)
            
            print("✅ All collections initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize collections: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise

    def _safely_create_collection(self, collection_name):
        """Create a collection with robust error handling."""
        try:
            print(f"🔍 Checking if collection '{collection_name}' exists...")
            
            # First try to get the collection directly - if it exists, this will work
            try:
                collection = AstraDBCollection(
                    collection_name=collection_name,
                    astra_db=self.db
                )
                
                # Test if the collection really exists by making a small query
                test = collection.find({}, options={"limit": 1})
                print(f"✅ Collection '{collection_name}' already exists")
                return collection
                
            except Exception as inner_e:
                # Collection might not exist, so we'll create it
                print(f"ℹ️ Collection '{collection_name}' may not exist: {inner_e}")
                print(f"🆕 Creating collection '{collection_name}'...")
                
                # Create the collection explicitly
                creation_result = self.db.create_collection(
                    collection_name=collection_name,
                    dimension=1536  # Default dimension for OpenAI embeddings
                )
                
                print(f"📊 Creation result: {creation_result}")
                
                if isinstance(creation_result, dict) and creation_result.get("status", {}).get("code") == 409:
                    print(f"⚠️ Collection '{collection_name}' already exists (409 conflict)")
                else:
                    print(f"✅ Created new collection: {collection_name}")
                    logger.info(f"Created new collection: {collection_name}")
                
                # Now get the collection object
                collection = AstraDBCollection(
                    collection_name=collection_name,
                    astra_db=self.db
                )
                return collection
                
        except Exception as e:
            error_msg = f"Error creating collection {collection_name}: {e}"
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
            # Modified to use vector_find without sort parameter
            results = await collection.vector_find(
                query_text,
                limit=limit,
                includeSimilarity=True  # Include the similarity score
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
            # Use find with just the limit parameter, no skip or sort
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
            
            print(f"📋 Retrieving entries from {collection_name} (page {page}, size {page_size})...")
            
            # Find documents - retrieve all and handle pagination in memory
            # This avoids using skip which requires sort parameter
            try:
                # First attempt: get just what we need for this page
                results = await collection.find(
                    filter={},
                    options={"limit": page_size}
                )
                
                # If we need a different page, handle it differently
                if page > 1:
                    # Get all entries we need
                    all_results = await collection.find(
                        filter={},
                        options={"limit": page * page_size}
                    )
                    
                    # Manual pagination in memory
                    start_idx = (page - 1) * page_size
                    results = all_results[start_idx:start_idx + page_size] if start_idx < len(all_results) else []
            
            except Exception as inner_e:
                # Fallback approach if the above fails
                logger.warning(f"Using fallback approach for pagination: {inner_e}")
                all_results = await collection.find(
                    filter={},
                    options={}  # No options to avoid potential issues
                )
                
                # Manual pagination in memory
                start_idx = (page - 1) * page_size
                results = all_results[start_idx:start_idx + page_size] if start_idx < len(all_results) else []
            
            print(f"✅ Retrieved {len(results)} entries from {collection_name}")
            logger.info(f"Retrieved {len(results)} entries from {collection_name}")
            return results
            
        except Exception as e:
            error_msg = f"Error retrieving entries from {collection_name}: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            return []