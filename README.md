# SetlistAI

A RAG (Retrieval-Augmented Generation) system that enables natural language querying of live music performance data. Ask questions like "What was the longest Dark Star by Grateful Dead?" and receive accurate, data-grounded responses.

## Overview

SetlistAI is designed for live music lovers to explore expansive catalogs and get deep-cut recommendations. The system uses vector similarity search combined with a relational database to retrieve relevant setlist information, then leverages an LLM to generate natural language responses.

## Architecture

SetlistAI follows a RAG (Retrieval-Augmented Generation) architecture:

```
User Query → Query Embedding → Vector Search (ChromaDB)
                                    ↓
                            Retrieve Top-K Setlists
                                    ↓
                            Fetch Full Details (SQLite)
                                    ↓
                            Format Context → LLM (OpenAI)
                                    ↓
                            Natural Language Response
```

### Core Components

- **Data Collector**: Fetches setlist data from Setlist.fm API
- **Data Processor**: Transforms raw JSON into structured data
- **Database**: SQLite storage for artists, venues, setlists, and songs
- **Embeddings**: Generates vector embeddings using OpenAI's text-embedding-3-small
- **Retriever**: Implements RAG retrieval logic (vector search + database lookup)
- **LLM Generator**: Uses GPT-4o-mini to generate responses from retrieved context

### Data Flow

1. **Setup Phase**: Collect setlists from Setlist.fm API → Process and structure → Store in SQLite → Generate embeddings → Store in ChromaDB
2. **Query Phase**: User question → Generate query embedding → Vector similarity search → Fetch full setlist details → Format context → LLM generation → Response

## Technology Stack

- **Vector Store**: ChromaDB (embedded, local)
- **Database**: SQLite
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: OpenAI GPT-4o-mini
- **Data Source**: Setlist.fm API

## Setup

### Prerequisites

- Python 3.12+
- API keys:
  - `SETLISTFM_API_KEY` (from [setlist.fm](https://www.setlist.fm/settings/api))
  - `OPENAI_API_KEY` (from [OpenAI](https://platform.openai.com/api-keys))

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd setlist-ai
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
SETLISTFM_API_KEY=your_setlistfm_api_key
OPENAI_API_KEY=your_openai_api_key
```

5. Run initial setup to collect and process data:
```bash
python src/main.py --setup
```

This will:
- Collect setlists for default artists (Grateful Dead, Phish, Dead & Company)
- Process and store data in SQLite
- Generate embeddings and store in ChromaDB

You can specify custom artists:
```bash
python src/main.py --setup --artists "Grateful Dead" "Phish" --max-setlists 100
```

## Usage

### Interactive Mode

Start an interactive session:
```bash
python src/main.py
```

Example queries:
- "Which shows had Dark Star?"
- "What was played as an encore on July 5, 2015?"
- "How many shows were at Soldier Field?"
- "What songs did they play most often?"
- "Show me all performances from the Fare Thee Well tour"

### Single Query

Ask a single question:
```bash
python src/main.py --query "Which shows had Dark Star?"
```

### Verbose Mode

See detailed retrieval information:
```bash
python src/main.py --query "Which shows had Dark Star?" --verbose
```

Or enable in interactive mode:
```
You: verbose on
```

## Database Schema

The system uses a relational schema with the following tables:

- **artists**: Artist information (name, MusicBrainz ID)
- **venues**: Venue details (name, city, country)
- **setlists**: Concert information (artist, venue, date, tour, embedding text)
- **songs**: Song details (name, position, encore status) linked to setlists

## Key Features

- **Semantic Search**: Uses vector embeddings to find semantically similar setlists, not just keyword matches
- **Two-Stage Retrieval**: Fast vector search identifies candidates, then database provides full details
- **Natural Language Interface**: Ask questions in plain English
- **Data-Grounded Responses**: All answers are based on actual setlist data, not model memory
- **Extensible Design**: Built with production scaling in mind

## Project Structure

```
setlist-ai/
├── src/
│   ├── main.py           # CLI entry point
│   ├── config.py         # Configuration management
│   ├── data_collector.py # Setlist.fm API client
│   ├── data_processor.py # Data transformation
│   ├── database.py       # SQLite operations
│   ├── embeddings.py    # Vector embedding generation
│   ├── retriever.py     # RAG retrieval logic
│   └── llm.py           # LLM response generation
├── data/
│   ├── raw/             # Raw JSON from API
│   ├── processed/       # Processed JSON
│   ├── setlistai.db     # SQLite database
│   └── chroma_db/       # ChromaDB vector store
└── requirements.txt     # Python dependencies
```

## Design Philosophy

SetlistAI is built as an MVP with a clear path to production:

- **MVP**: CLI interface, SQLite, ChromaDB, OpenAI API
- **Production Infrastructure**: Web interface, PostgreSQL, Pinecone, fine-tuned models, MLOps infrastructure

## Cost Considerations

The MVP is designed to be cost-effective:
- Embeddings: ~$0.02 per 1M tokens (text-embedding-3-small)
- LLM: GPT-4o-mini for development (~$0.15 per 1M input tokens)
- Expected MVP development cost: < $5

