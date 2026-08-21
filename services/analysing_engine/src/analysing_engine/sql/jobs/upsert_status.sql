INSERT INTO jobs (
    job_id,
    stage,
    status,
    error_code,
    updated_at
)
VALUES (
    %(job_id)s,
    %(stage)s,
    %(status)s,
    %(error_code)s,
    NOW()
)
ON CONFLICT (job_id, stage)
DO UPDATE SET
    status = EXCLUDED.status,
    error_code = EXCLUDED.error_code,
    updated_at = NOW();