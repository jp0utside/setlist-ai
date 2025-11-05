#!/bin/bash

echo "=== SetlistAI Setup ==="
echo ""
echo "Step 1: Collecting data from Setlist.fm..."
python3 src/data_collector.py

echo ""
echo "Step 2: Processing raw data..."
python3 src/data_processor.py

echo ""
echo "Step 3: Creating database and inserting data..."
python3 src/database.py

echo ""
echo "Step 4: Generating embeddings..."
python3 src/embeddings.py

echo ""
echo "=== Setup Complete! ==="