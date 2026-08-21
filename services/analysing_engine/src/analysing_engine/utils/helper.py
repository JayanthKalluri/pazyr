import uuid


def generate_flow_id() -> uuid.UUID:
    """
    Generate a unique identifier for an ingestion flow.
    """
    return uuid.uuid4()

    