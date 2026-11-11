-- Official Knowledge Database Schema

CREATE TABLE IF NOT EXISTS official_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    source_url TEXT,
    ingested_at TEXT NOT NULL,
    quarantined INTEGER NOT NULL DEFAULT 0 CHECK (quarantined IN (0, 1)),
    quarantine_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_official_documents_project
    ON official_documents(project_id, quarantined);

CREATE TABLE IF NOT EXISTS official_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER NOT NULL,
    project_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    faiss_vector_id INTEGER NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES official_documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_official_chunks_lookup
    ON official_chunks(project_id, doc_id, chunk_index);

CREATE INDEX IF NOT EXISTS idx_official_chunks_faiss
    ON official_chunks(project_id, faiss_vector_id);

