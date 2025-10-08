from src.config import config

print("Testing configuration...")
print(f"✓ Setlist.fm API Key: {'*' * 20}{config.SETLISTFM_API_KEY[-4:]}")
print(f"✓ OpenAI API Key: {'*' * 20}{config.OPENAI_API_KEY[-4:]}")
print(f"✓ Database path: {config.SQLITE_DB_PATH}")
print(f"✓ Vector DB path: {config.CHROMA_DB_PATH}")
print(f"✓ Embedding model: {config.EMBEDDING_MODEL}")
print(f"✓ LLM model: {config.LLM_MODEL}")

try:
    config.validate()
    print("\n✅ Configuration valid!")
except ValueError as e:
    print(f"\n❌ Configuration error: {e}")