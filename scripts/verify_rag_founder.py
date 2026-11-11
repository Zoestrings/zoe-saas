"""Standalone verification script for ONELOVE RAG index retrieval."""

import sys
from pathlib import Path
from zoe.knowledge.retriever import search

def main():
    query = "Who is the founder of the project?"
    print(f"Querying FAISS index for project 'onelove' with: '{query}'\n")

    chunks = search(
        project_id="onelove",
        query=query,
        top_k=3,
        db_path="data/official_knowledge/official_knowledge.db",
        index_dir="data/indexes",
    )

    print(f"Retrieved {len(chunks)} chunk(s) from FAISS index:\n")
    found_founder = False
    for i, c in enumerate(chunks, 1):
        print(f"==================== CHUNK {i} (Score: {c.score:.4f}) ====================")
        print(c.content.strip())
        print()
        if "captain robbie olson" in c.content.lower() or "captain robert olson" in c.content.lower():
            found_founder = True

    if not found_founder:
        print("[ERROR] 'Captain Robbie Olson' was NOT found in the top retrieved chunks!")
        sys.exit(1)

    print("[SUCCESS] Top retrieved chunks successfully contain 'Captain Robbie Olson'!")
    sys.exit(0)

if __name__ == "__main__":
    main()

