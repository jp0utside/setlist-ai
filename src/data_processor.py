from typing import List, Dict, Optional
from datetime import datetime
import json
from tqdm import tqdm


class SetlistProcessor:
    
    def process_setlist(self, raw_setlist: Dict) -> Optional[Dict]:
        """
        Extract and structure key information from raw setlist
        Returns None if setlist is invalid or has no songs
        """
        try:
            # Extract basic info
            setlist_id = raw_setlist.get("id")
            artist_name = raw_setlist.get("artist", {}).get("name")
            artist_mbid = raw_setlist.get("artist", {}).get("mbid")
            
            # Venue information
            venue = raw_setlist.get("venue", {})
            venue_name = venue.get("name")
            city_data = venue.get("city", {})
            city = city_data.get("name")
            country = city_data.get("country", {}).get("name")
            
            # Date (convert from DD-MM-YYYY to YYYY-MM-DD)
            event_date_str = raw_setlist.get("eventDate")
            event_date = self._convert_date(event_date_str) if event_date_str else None
            
            # Tour name (optional)
            tour = raw_setlist.get("tour", {})
            tour_name = tour.get("name") if isinstance(tour, dict) else None
            
            # Extract songs from nested structure
            songs_list, total_encores = self._extract_songs(raw_setlist)
            
            # Skip if no songs
            if not songs_list:
                return None
            
            # Build structured dict
            processed = {
                "setlist_id": setlist_id,
                "artist_name": artist_name,
                "artist_mbid": artist_mbid,
                "venue_name": venue_name,
                "city": city,
                "country": country,
                "event_date": event_date,
                "tour_name": tour_name,
                "songs": songs_list,
                "total_songs": len(songs_list),
                "total_encores": total_encores
            }
            
            return processed
            
        except Exception as e:
            print(f"✗ Error processing setlist: {e}")
            return None
    
    def _convert_date(self, date_string: str) -> str:
        """
        Convert date from DD-MM-YYYY to YYYY-MM-DD
        """
        try:
            # Parse DD-MM-YYYY
            date_obj = datetime.strptime(date_string, "%d-%m-%Y")
            # Return YYYY-MM-DD
            return date_obj.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"✗ Error converting date '{date_string}': {e}")
            return date_string  # Return original if conversion fails
    
    def _extract_songs(self, raw_setlist: Dict) -> tuple[List[Dict], int]:
        """
        Extract songs from nested sets structure
        Returns: (list of songs, count of encore songs)
        """
        songs_list = []
        total_encores = 0
        position = 1
        
        # Navigate the nested structure
        sets = raw_setlist.get("sets", {})
        set_list = sets.get("set", [])
        
        for set_obj in set_list:
            # Check if this is an encore set
            is_encore = "encore" in set_obj and set_obj["encore"] >= 1
            
            # Get songs from this set
            songs = set_obj.get("song", [])
            
            for song in songs:
                song_name = song.get("name")
                
                if song_name:
                    songs_list.append({
                        "name": song_name,
                        "position": position,
                        "is_encore": is_encore
                    })
                    
                    if is_encore:
                        total_encores += 1
                    
                    position += 1
        
        return songs_list, total_encores
    
    def create_embedding_text(self, processed_setlist: Dict) -> str:
        """
        Create rich text representation for embedding
        Includes context that helps with semantic search
        """
        parts = []
        
        # Artist
        if processed_setlist.get("artist_name"):
            parts.append(f"Artist: {processed_setlist['artist_name']}")
        
        # Date
        if processed_setlist.get("event_date"):
            parts.append(f"Date: {processed_setlist['event_date']}")
        
        # Venue and location
        venue_parts = []
        if processed_setlist.get("venue_name"):
            venue_parts.append(processed_setlist["venue_name"])
        if processed_setlist.get("city"):
            venue_parts.append(processed_setlist["city"])
        if processed_setlist.get("country"):
            venue_parts.append(processed_setlist["country"])
        
        if venue_parts:
            parts.append(f"Venue: {', '.join(venue_parts)}")
        
        # Tour
        if processed_setlist.get("tour_name"):
            parts.append(f"Tour: {processed_setlist['tour_name']}")
        
        # Separate regular songs from encores
        regular_songs = []
        encore_songs = []
        
        for song in processed_setlist.get("songs", []):
            if song["is_encore"]:
                encore_songs.append(song["name"])
            else:
                regular_songs.append(song["name"])
        
        # Main setlist
        if regular_songs:
            parts.append(f"Setlist: {', '.join(regular_songs)}")
        
        # Encores
        if encore_songs:
            parts.append(f"Encores: {', '.join(encore_songs)}")
        
        # Total songs
        parts.append(f"Total songs: {processed_setlist['total_songs']}")
        
        return "\n".join(parts)
    
    def batch_process(self, raw_setlists: List[Dict]) -> List[Dict]:
        """
        Process multiple setlists
        Adds embedding_text to each processed setlist
        """
        processed_list = []
        
        print(f"\nProcessing {len(raw_setlists)} setlists...")
        
        for raw_setlist in tqdm(raw_setlists, desc="Processing"):
            processed = self.process_setlist(raw_setlist)
            
            if processed:
                # Add embedding text
                processed["embedding_text"] = self.create_embedding_text(processed)
                processed_list.append(processed)
        
        print(f"✓ Successfully processed {len(processed_list)} setlists")
        print(f"✗ Skipped {len(raw_setlists) - len(processed_list)} invalid setlists")
        
        return processed_list


if __name__ == "__main__":
    # Test the processor
    import json
    from pathlib import Path
    
    # Load test data
    test_file = Path("data/raw/test_setlists.json")
    
    if not test_file.exists():
        print(f"✗ Test file not found: {test_file}")
        print("Run data_collector.py first to generate test data")
        exit(1)
    
    with open(test_file) as f:
        raw_setlists = json.load(f)
    
    processor = SetlistProcessor()
    
    # Process first setlist
    print("=" * 60)
    print("PROCESSING SINGLE SETLIST")
    print("=" * 60)
    
    processed = processor.process_setlist(raw_setlists[0])
    
    if processed:
        print("\nProcessed setlist:")
        print(json.dumps(processed, indent=2))
        
        print("\n" + "=" * 60)
        print("EMBEDDING TEXT")
        print("=" * 60)
        text = processor.create_embedding_text(processed)
        print(text)
    
    # Process all setlists
    print("\n" + "=" * 60)
    print("BATCH PROCESSING")
    print("=" * 60)
    
    all_processed = processor.batch_process(raw_setlists)
    
    # Save processed data
    output_file = Path("data/processed/test_setlists_processed.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_processed, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved processed data to: {output_file}")
    
    # Show sample embedding text
    if all_processed:
        print("\n" + "=" * 60)
        print("SAMPLE EMBEDDING TEXT")
        print("=" * 60)
        print(all_processed[0]["embedding_text"])