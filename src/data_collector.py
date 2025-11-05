
import requests
import time
import json
import math
from typing import List, Dict, Optional
from pathlib import Path
from tqdm import tqdm
from config import config

class SetlistFMClient:
    BASE_URL = "https://api.setlist.fm/rest/1.0/" #setlistfm api endpoint
    RATE_LIMIT_DELAY = 1.0 #delay between calls

    def __init__(self):
        self.api_key = config.SETLISTFM_API_KEY
        self.headers = {
            "x-api-key": config.SETLISTFM_API_KEY,
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_artist(self, artistName: str) -> Optional[dict]:
        url = self.BASE_URL + "search/artists/"
        query_params = {"artistName": artistName, "sort": "relevance"}

        try:
            response = self.session.get(url, params=query_params)
            response.raise_for_status()

            data = response.json()

            if data.get("artist") and len(data["artist"]) > 0:
                artist = data["artist"][0]
                print(f"✓ Found artist: {artist['name']} (mbid: {artist['mbid']})")
                return artist
            else:
                print(f"No artist found for search: {artistName}")
                return None

        except requests.exceptions.RequestException as e:
            print("✗ Error in SetlistFMClient artist search: ", e)
            return None
    
    def get_artist_setlists(self, artist_mbid: str, max_setlists: int = 100) -> List[Dict]:
        print(f"Fetching setlists for artist MBID: {artist_mbid}")
        print(f"Target: {max_setlists} setlists")

        items_per_page = 20
        all_setlists = []
        page = 1
        for i in range(math.ceil(max_setlists/items_per_page)):
            url = self.BASE_URL + f"artist/{artist_mbid}/setlists"
            params = {"p": page}

            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                setlists = data.get("setlist", [])

                if not setlists:
                    print(f"✓ No more setlists for page {page}")
                    break

                all_setlists.extend(setlists)
                if len(all_setlists) > max_setlists:
                    all_setlists = all_setlists[:max_setlists]
                    break

                page+=1
                time.sleep(self.RATE_LIMIT_DELAY)
            
            except requests.exceptions.RequestException as e:
                print(f"✗ Error in SetlistFMClient artist setlist page {page}: {e}")
                return []

        if len(all_setlists) > 0:
            return all_setlists
        else:
            print(f"No setlists found for mbid {artist_mbid}")
            return []
    
    def save_raw_data(self, data: List[Dict], filename: str):
        fp = Path("data/raw") / filename
        fp.parent.mkdir(parents=True, exist_ok=True)

        with open(fp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved raw data to: {fp}")

if __name__ == "__main__":
    #Instantiate SetlistFMClient
    cli = SetlistFMClient()

    #Search for artist
    artist = cli.search_artist("Grateful Dead")
    time.sleep(cli.RATE_LIMIT_DELAY)

    if artist:
        #Get setlists
        setlists = cli.get_artist_setlists(artist["mbid"], max_setlists=5)

        print(setlists)

        #Save to File
        if setlists:
            cli.save_raw_data(setlists, "test_setlists.json")

            print(f"✅ Test Successful! Check data/raw/test_setlists.json")










