"""
SQLite database operations
Schema design for setlist data
"""

import sqlite3
from typing import List, Dict, Optional
from pathlib import Path
from config import config


class SetlistDatabase:
    
    def __init__(self):
        self.db_path = config.SQLITE_DB_PATH
        self.conn = None
    
    def connect(self):
        """Create database connection"""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return dict-like rows
        
        # Enable foreign keys (not enabled by default in SQLite)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        print(f"✓ Connected to database: {self.db_path}")
    
    def create_schema(self):
        """
        Create tables for setlist data
        """
        cursor = self.conn.cursor()
        
        # Artists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artists (
                artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mbid TEXT UNIQUE NOT NULL
            )
        """)
        
        # Venues table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS venues (
                venue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT,
                country TEXT
            )
        """)
        
        # Setlists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS setlists (
                setlist_id TEXT PRIMARY KEY,
                artist_id INTEGER NOT NULL,
                venue_id INTEGER NOT NULL,
                event_date TEXT NOT NULL,
                tour_name TEXT,
                total_songs INTEGER NOT NULL,
                embedding_text TEXT,
                FOREIGN KEY (artist_id) REFERENCES artists(artist_id),
                FOREIGN KEY (venue_id) REFERENCES venues(venue_id)
            )
        """)
        
        # Songs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                song_id INTEGER PRIMARY KEY AUTOINCREMENT,
                setlist_id TEXT NOT NULL,
                song_name TEXT NOT NULL,
                position INTEGER NOT NULL,
                is_encore INTEGER NOT NULL,
                FOREIGN KEY (setlist_id) REFERENCES setlists(setlist_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_artists_mbid 
            ON artists(mbid)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_setlists_artist 
            ON setlists(artist_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_setlists_date 
            ON setlists(event_date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_songs_setlist 
            ON songs(setlist_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_songs_name 
            ON songs(song_name)
        """)
        
        self.conn.commit()
        print("✓ Database schema created")
    
    def _get_or_create_artist(self, name: str, mbid: str) -> int:
        """
        Get existing artist or create new one
        Returns artist_id
        """
        cursor = self.conn.cursor()
        
        # Try to find existing artist
        cursor.execute(
            "SELECT artist_id FROM artists WHERE mbid = ?",
            (mbid,)
        )
        row = cursor.fetchone()
        
        if row:
            return row['artist_id']
        
        # Create new artist
        cursor.execute(
            "INSERT INTO artists (name, mbid) VALUES (?, ?)",
            (name, mbid)
        )
        return cursor.lastrowid
    
    def _get_or_create_venue(self, name: str, city: str, country: str) -> int:
        """
        Get existing venue or create new one
        Returns venue_id
        """
        cursor = self.conn.cursor()
        
        # Try to find existing venue (match on name + city)
        cursor.execute(
            "SELECT venue_id FROM venues WHERE name = ? AND city = ?",
            (name, city)
        )
        row = cursor.fetchone()
        
        if row:
            return row['venue_id']
        
        # Create new venue
        cursor.execute(
            "INSERT INTO venues (name, city, country) VALUES (?, ?, ?)",
            (name, city, country)
        )
        return cursor.lastrowid
    
    def insert_setlist(self, processed_setlist: Dict) -> str:
        """
        Insert processed setlist with related data
        Returns setlist_id
        """
        cursor = self.conn.cursor()
        
        try:
            # Get or create artist
            artist_id = self._get_or_create_artist(
                processed_setlist['artist_name'],
                processed_setlist['artist_mbid']
            )
            
            # Get or create venue
            venue_id = self._get_or_create_venue(
                processed_setlist['venue_name'],
                processed_setlist['city'],
                processed_setlist['country']
            )
            
            # Insert setlist
            cursor.execute("""
                INSERT INTO setlists 
                (setlist_id, artist_id, venue_id, event_date, tour_name, 
                 total_songs, embedding_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                processed_setlist['setlist_id'],
                artist_id,
                venue_id,
                processed_setlist['event_date'],
                processed_setlist.get('tour_name'),
                processed_setlist['total_songs'],
                processed_setlist.get('embedding_text')
            ))
            
            # Insert songs
            for song in processed_setlist['songs']:
                cursor.execute("""
                    INSERT INTO songs 
                    (setlist_id, song_name, position, is_encore)
                    VALUES (?, ?, ?, ?)
                """, (
                    processed_setlist['setlist_id'],
                    song['name'],
                    song['position'],
                    1 if song['is_encore'] else 0
                ))
            
            self.conn.commit()
            return processed_setlist['setlist_id']
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            # Setlist probably already exists
            print(f"✗ Error inserting setlist {processed_setlist['setlist_id']}: {e}")
            return None
        except Exception as e:
            self.conn.rollback()
            print(f"✗ Unexpected error inserting setlist: {e}")
            return None
    
    def get_setlist_by_id(self, setlist_id: str) -> Optional[Dict]:
        """
        Retrieve complete setlist data by ID
        Returns dict with all information including songs
        """
        cursor = self.conn.cursor()
        
        # Get setlist with artist and venue info
        cursor.execute("""
            SELECT 
                s.setlist_id,
                s.event_date,
                s.tour_name,
                s.total_songs,
                s.embedding_text,
                a.name as artist_name,
                a.mbid as artist_mbid,
                v.name as venue_name,
                v.city,
                v.country
            FROM setlists s
            JOIN artists a ON s.artist_id = a.artist_id
            JOIN venues v ON s.venue_id = v.venue_id
            WHERE s.setlist_id = ?
        """, (setlist_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Convert to dict
        setlist = dict(row)
        
        # Get songs for this setlist
        cursor.execute("""
            SELECT song_name, position, is_encore
            FROM songs
            WHERE setlist_id = ?
            ORDER BY position
        """, (setlist_id,))
        
        songs = []
        for song_row in cursor.fetchall():
            songs.append({
                'name': song_row['song_name'],
                'position': song_row['position'],
                'is_encore': bool(song_row['is_encore'])
            })
        
        setlist['songs'] = songs
        
        return setlist
    
    def get_setlists_by_ids(self, setlist_ids: List[str]) -> List[Dict]:
        """
        Retrieve multiple setlists by IDs
        Returns list of complete setlist dicts
        """
        setlists = []
        for setlist_id in setlist_ids:
            setlist = self.get_setlist_by_id(setlist_id)
            if setlist:
                setlists.append(setlist)
        return setlists
    
    def get_all_setlist_ids(self) -> List[str]:
        """
        Get list of all setlist IDs in database
        Useful for generating embeddings
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT setlist_id FROM setlists")
        return [row['setlist_id'] for row in cursor.fetchall()]
    
    def count_setlists(self) -> int:
        """Count total setlists in database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM setlists")
        return cursor.fetchone()['count']
    
    def count_artists(self) -> int:
        """Count total artists in database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM artists")
        return cursor.fetchone()['count']
    
    def count_venues(self) -> int:
        """Count total venues in database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM venues")
        return cursor.fetchone()['count']
    
    def count_songs(self) -> int:
        """Count total songs in database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM songs")
        return cursor.fetchone()['count']
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("✓ Database connection closed")


if __name__ == "__main__":
    # Test the database
    import json
    from pathlib import Path
    
    # 1. Create and connect to database
    print("="*60)
    print("CREATING DATABASE")
    print("="*60)
    
    db = SetlistDatabase()
    db.connect()
    db.create_schema()
    
    # 2. Load processed data
    processed_file = Path("data/processed/test_setlists_processed.json")
    
    if not processed_file.exists():
        print(f"\n✗ Processed data not found: {processed_file}")
        print("Run data_processor.py first to generate processed data")
        db.disconnect()
        exit(1)
    
    with open(processed_file) as f:
        processed_setlists = json.load(f)
    
    # 3. Insert setlists
    print("\n" + "="*60)
    print("INSERTING SETLISTS")
    print("="*60)
    
    inserted_ids = []
    for setlist in processed_setlists:
        setlist_id = db.insert_setlist(setlist)
        if setlist_id:
            print(f"✓ Inserted setlist: {setlist_id}")
            inserted_ids.append(setlist_id)
        else:
            print(f"✗ Failed to insert setlist")
    
    print(f"\n✓ Successfully inserted {len(inserted_ids)} setlists")
    
    # 4. Test retrieval
    print("\n" + "="*60)
    print("TESTING RETRIEVAL")
    print("="*60)
    
    if inserted_ids:
        test_id = inserted_ids[0]
        print(f"\nRetrieving setlist: {test_id}")
        
        retrieved = db.get_setlist_by_id(test_id)
        
        if retrieved:
            print(f"\n✓ Successfully retrieved setlist")
            print(f"\nArtist: {retrieved['artist_name']}")
            print(f"Date: {retrieved['event_date']}")
            print(f"Venue: {retrieved['venue_name']}, {retrieved['city']}, {retrieved['country']}")
            print(f"Total songs: {retrieved['total_songs']}")
            print(f"\nFirst 5 songs:")
            for song in retrieved['songs'][:5]:
                encore_marker = " (ENCORE)" if song['is_encore'] else ""
                print(f"  {song['position']}. {song['name']}{encore_marker}")
    
    # 5. Test batch retrieval
    print("\n" + "="*60)
    print("TESTING BATCH RETRIEVAL")
    print("="*60)
    
    if len(inserted_ids) >= 3:
        test_ids = inserted_ids[:3]
        batch_results = db.get_setlists_by_ids(test_ids)
        print(f"\n✓ Retrieved {len(batch_results)} setlists in batch")
        for setlist in batch_results:
            print(f"  - {setlist['artist_name']} on {setlist['event_date']}")
    
    # 6. Show statistics
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    
    print(f"\nTotal artists: {db.count_artists()}")
    print(f"Total venues: {db.count_venues()}")
    print(f"Total setlists: {db.count_setlists()}")
    print(f"Total songs: {db.count_songs()}")
    
    # 7. Cleanup
    db.disconnect()
    
    print("\n" + "="*60)
    print("✅ DATABASE TEST COMPLETE!")
    print("="*60)
    print(f"\nDatabase file created at: {config.SQLITE_DB_PATH}")
    print("You can inspect it with: sqlite3 data/setlistai.db")
