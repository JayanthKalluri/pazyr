INSERT INTO documents (
    id,
    source_url,
    title,
    content,
    summary,
    metadata
)
VALUES (
    %(id)s,
    %(source_url)s,
    %(title)s,
    %(content)s,
    %(summary)s,
    %(metadata)s
);