import shutil
from pathlib import Path
from zoe.db.connections import open_official_knowledge_db
from zoe.knowledge.ingestion import ingest_document

db_file = Path("data/official_knowledge/official_knowledge.db")
conn = open_official_knowledge_db(db_file)
conn.execute("DELETE FROM official_chunks WHERE project_id = 'onelove'")
conn.execute("DELETE FROM official_documents WHERE project_id = 'onelove'")
conn.commit()
conn.close()

index_dir = Path("data/indexes/onelove")
if index_dir.exists():
    shutil.rmtree(index_dir)
index_dir.mkdir(parents=True, exist_ok=True)

res = ingest_document("data/knowledge/onelove_info.txt", "onelove")
print("Ingestion result:", res)

index_file = index_dir / "index.faiss"
print("FAISS index exists:", index_file.exists(), "Size:", index_file.stat().st_size if index_file.exists() else 0)

