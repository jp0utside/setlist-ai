import os
from dotenv import load_dotenv
import requests
from openai import OpenAI

load_dotenv()

# Test Setlist.fm API
print("Testing Setlist.fm API...")
setlistfm_key = os.getenv("SETLISTFM_API_KEY")
if not setlistfm_key:
    print("❌ SETLISTFM_API_KEY not found in .env")
else:
    headers = {"x-api-key": setlistfm_key, "Accept": "application/json"}
    response = requests.get(
        "https://api.setlist.fm/rest/1.0/search/artists?artistName=Grateful+Dead",
        headers=headers
    )
    if response.status_code == 200:
        print("✅ Setlist.fm API working!")
    else:
        print(f"❌ Setlist.fm API error: {response.status_code}")

# Test OpenAI API
print("\nTesting OpenAI API...")
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("❌ OPENAI_API_KEY not found in .env")
else:
    try:
        client = OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API works!'"}],
            max_tokens=10
        )
        print(f"✅ OpenAI API working! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")

print("\n🎉 Setup complete! Ready to start building.")
