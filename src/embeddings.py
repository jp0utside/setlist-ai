"""
Class to manage embeddings for setlist data
"""
from typing import List, Dict
from tqdm import tqdm
import chromadb
from openai import OpenAI
from config import config


class EmbeddingManager:
    def __init__(self):
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.chroma_client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)

        self.collection = self.chroma_client.get_or_create_collection(
            name="setlists", 
            metadata={"hnsw:space": "cosine"})
        
    def generate_embedding(self, text: str) -> list[float]:
        try:
            response = self.openai_client.embeddings.create(
                model = "text-embedding-3-small",
                input = text
            )
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def add_setlist(self, setlist_id: str, embedding_text: str):
        embedding = self.generate_embedding(embedding_text)

        if embedding is None:
            print(f"Error generating embedding for setlist {setlist_id}")
            return

        self.collection.add(
            ids = [setlist_id],
            embeddings = [embedding],
            documents = [embedding_text]
        )
    
    def batch_add_setlists(self, setlists: List[Dict]):
        # Batch size for OpenAI API (they support up to 2048)
        batch_size = 100

        # Process in batches with progress bar
        for i in tqdm(range(0, len(setlists), batch_size), desc="Processing batches"):
            batch = setlists[i:i + batch_size]
            
            # Prepare batch data
            batch_ids = []
            batch_texts = []
            
            for setlist in batch:
                batch_ids.append(str(setlist['setlist_id']))
                batch_texts.append(setlist['embedding_text'])
            
            try:
                # Generate embeddings for entire batch in one API call
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch_texts
                )
                
                # Extract embeddings
                batch_embeddings = [item.embedding for item in response.data]
                
                # Add entire batch to ChromaDB
                self.collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_texts
                )

            except Exception as e:
                print(f"\nError processing batch starting at index {i}: {e}")
                # Fall back to individual processing for this batch
                print("Falling back to individual processing...")
                for setlist in batch:
                    try:
                        self.add_setlist(
                            str(setlist['setlist_id']),
                            setlist['embedding_text']
                        )
                    except Exception as e2:
                        print(f"Failed to add setlist {setlist['setlist_id']}: {e2}")
        
        print(f"Batch processing complete")
    
    def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        query_embedding = self.generate_embedding(query)

        if query_embedding is None:
            print("Failed to generate query embedding")
            return []

        results = self.collection.query(
            query_embeddings = [query_embedding],
            n_results = top_k
        )

        formatted_results = []

        # Extract results from ChromaDB payload
        ids = results['ids'][0] if results['ids'] else []
        distances = results['distances'][0] if results['distances'] else []
        documents = results['documents'][0] if results['documents'] else []
        
        for setlist_id, distance, document in zip(ids, distances, documents):
            # Convert distance to similarity score (0-1 range, higher is better)
            # ChromaDB uses cosine distance, so similarity = 1 - (distance / 2)
            similarity = 1 - (distance / 2)
            
            formatted_results.append({
                'setlist_id': setlist_id,
                'distance': distance,
                'similarity': similarity,
                'text': document
            })
        
        return formatted_results
    
    def get_collection_count(self) -> int:
        return self.collection.count()

if __name__ == "__main__":
    from database import SetlistDatabase
    
    # 1. Initialize
    print("="*60)
    print("INITIALIZING EMBEDDING MANAGER")
    print("="*60)
    
    embedding_mgr = EmbeddingManager()
    print(f"ChromaDB collection: {embedding_mgr.collection.name}")
    print(f"Current count: {embedding_mgr.get_collection_count()}")
    
    # 2. Get setlists from database
    print("\n" + "="*60)
    print("LOADING SETLISTS FROM DATABASE")
    print("="*60)
    
    db = SetlistDatabase()
    db.connect()
    
    setlist_ids = db.get_all_setlist_ids()
    print(f"✓ Found {len(setlist_ids)} setlists in database")
    
    # Get full data for each setlist
    setlists = []
    for setlist_id in setlist_ids:
        setlist = db.get_setlist_by_id(setlist_id)
        if setlist and setlist.get('embedding_text'):
            setlists.append(setlist)
        else:
            print(f"✗ Skipping setlist {setlist_id} (no embedding text)")
    
    print(f"Loaded {len(setlists)} setlists with embedding text")
    
    # 3. Generate and store embeddings
    print("\n" + "="*60)
    print("GENERATING EMBEDDINGS")
    print("="*60)
    print(f"Processing {len(setlists)} setlists...")
    # Cost: ~$0.00002 per setlist with text-embedding-3-small
    estimated_cost = len(setlists) * 0.00002
    print(f"Estimated cost: ~${estimated_cost:.4f}")
    
    if setlists:
        embedding_mgr.batch_add_setlists(setlists)
        print(f"\nTotal embeddings in ChromaDB: {embedding_mgr.get_collection_count()}")
    else:
        print("No setlists to process")
    
    # 4. Test similarity search
    print("\n" + "="*60)
    print("TESTING SIMILARITY SEARCH")
    print("="*60)
    
    test_queries = [
        "Shows with Dark Star",
        "Acoustic performances",
        "Long encore songs",
        "1977 concerts",
        "Madison Square Garden shows"
    ]
    
    for query in test_queries:
        print(f"\n{'─'*60}")
        print(f"Query: '{query}'")
        print(f"{'─'*60}")
        
        results = embedding_mgr.search_similar(query, top_k=3)
        
        if results:
            print(f"Top {len(results)} matches:")
            for i, result in enumerate(results, 1):
                # Get setlist details from database
                setlist = db.get_setlist_by_id(result['setlist_id'])
                if setlist:
                    print(f"\n  {i}. {setlist['artist_name']} - {setlist['event_date']}")
                    print(f"     Venue: {setlist['venue_name']}, {setlist['city']}")
                    print(f"     Similarity: {result['similarity']:.3f} (distance: {result['distance']:.3f})")
                    print(f"     Songs: {', '.join([s['name'] for s in setlist['songs'][:5]])}...")
        else:
            print("  No results found")
    
    db.disconnect()
    
    print("\n" + "="*60)
    print("✅ EMBEDDINGS TEST COMPLETE!")
    print("="*60)
    print(f"\nChromaDB stored at: {config.CHROMA_DB_PATH}")
    print(f"Total embeddings: {embedding_mgr.get_collection_count()}")

