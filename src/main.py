"""
CLI entry point for SetlistAI
Handles user interaction and orchestrates components
"""

import argparse
import sys
from pathlib import Path

from retriever import SetlistRetriever
from llm import LLMGenerator
from data_collector import SetlistFMClient
from data_processor import SetlistProcessor
from database import SetlistDatabase
from embeddings import EmbeddingManager


class SetlistAI:
    """Main application class"""
    
    def __init__(self):
        """Initialize all components"""
        print("🎸 Initializing SetlistAI...")
        
        self.retriever = SetlistRetriever()
        self.llm = LLMGenerator()
        
        print("✓ SetlistAI ready!\n")
    
    def query(self, question: str, verbose: bool = False) -> str:
        """
        Main query pipeline
        
        Args:
            question: User's natural language question
            verbose: If True, show detailed retrieval info
            
        Returns:
            Generated response
        """
        if verbose:
            print(f"🔍 Searching for: {question}")
        
        # 1. Retrieve relevant setlists
        results = self.retriever.retrieve(question, top_k=5)
        
        if verbose:
            print(f"✓ Found {len(results)} relevant setlists")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['artist_name']} - {result['event_date']} "
                      f"(relevance: {result.get('similarity_score', 0):.2f})")
        
        # 2. Format context
        context = self.retriever.format_context(results)
        
        # 3. Generate response
        if verbose:
            print("🤖 Generating response...\n")
        
        response = self.llm.generate_response(question, context)
        
        return response
    
    def interactive_mode(self):
        """Interactive CLI loop"""
        print("="*60)
        print("🎸 SetlistAI - Interactive Mode")
        print("="*60)
        print("Ask questions about live music performances!")
        print("Type 'quit' or 'exit' to end the session")
        print("Type 'help' for example queries")
        print("Type 'verbose on/off' to toggle detailed output")
        print("="*60)
        print()
        
        verbose = False
        
        while True:
            try:
                # Get user input
                query = input("You: ").strip()
                
                # Handle special commands
                if not query:
                    continue
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Thanks for using SetlistAI!")
                    break
                
                if query.lower() == 'help':
                    self._show_help()
                    continue
                
                if query.lower().startswith('verbose'):
                    if 'on' in query.lower():
                        verbose = True
                        print("✓ Verbose mode enabled\n")
                    elif 'off' in query.lower():
                        verbose = False
                        print("✓ Verbose mode disabled\n")
                    continue
                
                # Process query
                response = self.query(query, verbose=verbose)
                
                # Display response
                print(f"\n🎸 SetlistAI:\n{response}\n")
                print("-"*60 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Thanks for using SetlistAI!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
    
    def setup(self, artists: list = None, max_per_artist: int = 100):
        """
        Initial data collection and setup
        
        Args:
            artists: List of artist names to collect
            max_per_artist: Maximum setlists per artist
        """
        print("="*60)
        print("🎸 SetlistAI Setup")
        print("="*60)
        print()
        
        # Default artists if none provided
        if artists is None:
            artists = ["Grateful Dead", "Phish", "Dead & Company"]
        
        # Initialize components
        collector = SetlistFMClient()
        processor = SetlistProcessor()
        db = SetlistDatabase()
        db.connect()
        db.create_schema()
        embedding_mgr = EmbeddingManager()
        
        # Track all processed setlists for embedding generation
        all_processed = []
        
        # Collect data for each artist
        for artist_name in artists:
            print(f"\n{'='*60}")
            print(f"📀 Collecting data for: {artist_name}")
            print(f"{'='*60}")
            
            # 1. Search artist
            artist = collector.search_artist(artist_name)
            if not artist:
                print(f"✗ Could not find artist: {artist_name}")
                continue
            
            # 2. Get setlists
            print(f"\n🎵 Fetching setlists...")
            raw_setlists = collector.get_artist_setlists(
                artist['mbid'], 
                max_setlists=max_per_artist
            )
            
            if not raw_setlists:
                print(f"✗ No setlists found for {artist_name}")
                continue
            
            # 3. Save raw data
            collector.save_raw_data(
                raw_setlists, 
                f"{artist_name.lower().replace(' ', '_')}_raw.json"
            )
            
            # 4. Process setlists
            print(f"\n⚙️  Processing setlists...")
            processed = processor.batch_process(raw_setlists)
            
            if not processed:
                print(f"✗ Failed to process setlists for {artist_name}")
                continue
            
            # 5. Insert into database
            print(f"\n💾 Storing in database...")
            inserted_count = 0
            for setlist in processed:
                setlist_id = db.insert_setlist(setlist)
                if setlist_id:
                    inserted_count += 1
                    all_processed.append(setlist)
            
            print(f"✓ Inserted {inserted_count}/{len(processed)} setlists")
        
        # 6. Generate embeddings for all setlists
        if all_processed:
            print(f"\n{'='*60}")
            print(f"🧠 Generating embeddings for {len(all_processed)} setlists...")
            print(f"{'='*60}")
            
            embedding_mgr.batch_add_setlists(all_processed)
            
            print(f"✓ Generated {embedding_mgr.get_collection_count()} embeddings")
        
        # 7. Show statistics
        print(f"\n{'='*60}")
        print("📊 Database Statistics")
        print(f"{'='*60}")
        print(f"  Artists:  {db.count_artists()}")
        print(f"  Venues:   {db.count_venues()}")
        print(f"  Setlists: {db.count_setlists()}")
        print(f"  Songs:    {db.count_songs()}")
        print(f"{'='*60}")
        
        db.disconnect()
        
        print("\n✅ Setup complete! You can now query SetlistAI.")
        print(f"   Run: python src/main.py\n")
    
    def _show_help(self):
        """Show example queries"""
        print("\n📖 Example Queries:")
        print("-"*60)
        examples = [
            "Which shows had Dark Star?",
            "What was played as an encore on July 5, 2015?",
            "How many shows were at Soldier Field?",
            "What songs did they play most often?",
            "Show me all performances from the Fare Thee Well tour",
            "Which venue had the longest setlists?"
        ]
        for example in examples:
            print(f"  • {example}")
        print("-"*60 + "\n")
    
    def cleanup(self):
        """Clean up resources"""
        self.retriever.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SetlistAI - Natural language queries for live music data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run setup (first time only)
  python src/main.py --setup
  
  # Interactive mode
  python src/main.py
  
  # Single query
  python src/main.py --query "Which shows had Dark Star?"
  
  # Setup with specific artists
  python src/main.py --setup --artists "Grateful Dead" "Phish"
        """
    )
    
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Run initial data collection and setup'
    )
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Ask a single question and exit'
    )
    
    parser.add_argument(
        '--artists',
        nargs='+',
        help='Artist names to collect (only with --setup)'
    )
    
    parser.add_argument(
        '--max-setlists',
        type=int,
        default=100,
        help='Maximum setlists per artist (default: 100)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )
    
    args = parser.parse_args()
    
    # Setup mode
    if args.setup:
        # Don't initialize full app for setup (it will fail if no data exists)
        app = SetlistAI.__new__(SetlistAI)  # Create instance without __init__
        app.setup(
            artists=args.artists,
            max_per_artist=args.max_setlists
        )
        return
    
    # Check if data exists
    db_path = Path("data/setlistai.db")
    if not db_path.exists():
        print("❌ No data found. Please run setup first:")
        print("   python src/main.py --setup\n")
        sys.exit(1)
    
    # Initialize application
    try:
        app = SetlistAI()
        
        # Single query mode
        if args.query:
            response = app.query(args.query, verbose=args.verbose)
            print(f"\n🎸 SetlistAI:\n{response}\n")
            app.cleanup()
            return
        
        # Interactive mode (default)
        app.interactive_mode()
        app.cleanup()
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()