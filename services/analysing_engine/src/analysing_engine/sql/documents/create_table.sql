CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    source_url TEXT,
    title TEXT,
    content TEXT,
    summary TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);