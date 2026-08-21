CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    error_code TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (job_id, stage)
);