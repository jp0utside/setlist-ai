"""
Class implementing RAG retrieval logic
Combines embedding search with database retrieval
"""
from embeddings import EmbeddingManager
from typing import List, Dict
from database import SetlistDatabase

class SetlistRetriever:
    def __init__(self):
        self.embedding_mgr = EmbeddingManager()
        self.db = SetlistDatabase()
        self.db.connect()
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        # Get query embeddings and retrieve similar setlists
        similar_results = self.embedding_mgr.search_similar(query, top_k)
        setlist_ids = [result['setlist_id'] for result in similar_results]

        # Get full setlists from database
        full_setlists = self.db.get_setlists_by_ids(setlist_ids)

        # Enrich with similarity scores
        for setlist in full_setlists:
            for result in similar_results:
                if result["setlist_id"] == setlist["setlist_id"]:
                    setlist["similarity_score"] = result["similarity"]
                    setlist["distance"] = result["distance"]
                    break

        return full_setlists
    
    def format_context(self, results: List[Dict]) -> str:
        if not results:
            return "No relevant setlists found."
        
        context_parts = ["Retrieved concert setlists:\n"]
        
        for i, setlist in enumerate(results, 1):
            # Header with artist, date, venue
            context_parts.append(
                f"\n{i}. {setlist['artist_name']} - {setlist['event_date']}\n"
            )
            
            # Venue details
            venue_info = f"   Venue: {setlist['venue_name']}"
            if setlist.get('city'):
                venue_info += f", {setlist['city']}"
            if setlist.get('country'):
                venue_info += f", {setlist['country']}"
            context_parts.append(venue_info + "\n")
            
            # Tour name if available
            if setlist.get('tour_name'):
                context_parts.append(f"   Tour: {setlist['tour_name']}\n")
            
            # Separate regular songs from encores
            regular_songs = []
            encore_songs = []
            
            for song in setlist.get('songs', []):
                if song['is_encore']:
                    encore_songs.append(song['name'])
                else:
                    regular_songs.append(song['name'])
            
            # Main setlist (limit to first 15 songs to save tokens)
            if regular_songs:
                song_list = ', '.join(regular_songs[:15])
                if len(regular_songs) > 15:
                    song_list += f"... ({len(regular_songs)} total songs)"
                context_parts.append(f"   Setlist: {song_list}\n")
            
            # Encores
            if encore_songs:
                context_parts.append(f"   Encores: {', '.join(encore_songs)}\n")
            
            # Total songs
            context_parts.append(f"   Total songs: {setlist['total_songs']}\n")
            
            # Similarity score (helpful for LLM to know relevance)
            if 'similarity_score' in setlist:
                context_parts.append(f"   Relevance: {setlist['similarity_score']:.2f}\n")
        
        return ''.join(context_parts)
    
    def close(self):
        self.db.disconnect()
    
if __name__ == "__main__":
    # Test the retriever
    print("="*60)
    print("TESTING SETLIST RETRIEVER")
    print("="*60)
    
    retriever = SetlistRetriever()
    
    test_queries = [
        "Shows with Dark Star",
        "Encores with Touch of Grey",
        "Long setlists from 2015",
        "Shows at Soldier Field",
        "Performances with Terrapin Station"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print(f"{'='*60}")
        
        # Retrieve
        results = retriever.retrieve(query, top_k=3)
        
        print(f"\nFound {len(results)} relevant setlists")
        
        # Format context
        context = retriever.format_context(results)
        
        print("\nFormatted Context for LLM:")
        print("-"*60)
        print(context)
    
    retriever.close()
    
    print("\n" + "="*60)
    print("✅ RETRIEVER TEST COMPLETE!")
    print("="*60)
