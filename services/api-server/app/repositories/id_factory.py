from uuid import uuid4


def prefixed_uuid(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"
