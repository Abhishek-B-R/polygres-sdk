"""Private query input validation and retry identity handling."""

from uuid import uuid4

from pydantic import ValidationError

from polygres._vendor.polygres_lib.context.models import DenseSearchRequest
from polygres.errors import PolygresValidationError


def validate_query_input(embedding, text, use_credits):
    try:
        DenseSearchRequest(
            collection="query", embedding=embedding, text=text, use_credits=use_credits
        )
    except ValidationError as exc:
        raise PolygresValidationError(str(exc)) from exc


def contains_query_text(payload):
    if not isinstance(payload, dict):
        return False
    if payload.get("text") is not None:
        return True
    if "plan" in payload:
        return contains_query_text(payload["plan"])
    if "kind" in payload:
        return contains_query_text(payload.get("branch")) or any(
            contains_query_text(child) for child in payload.get("branches", [])
        )
    return False


def query_transport(payload, idempotency_key=None):
    if not contains_query_text(payload):
        # Keep vector-only wire payloads compatible with earlier Runtime versions.
        return {k: v for k, v in payload.items() if k not in {"text", "use_credits"}}, None
    key = idempotency_key or str(uuid4())
    if not isinstance(key, str) or not key.strip() or len(key) > 200:
        raise PolygresValidationError("idempotency_key must contain 1 to 200 characters")
    return payload, {"Idempotency-Key": key}


def query_deadline(timeout):
    import time

    import httpx

    seconds = timeout.read if isinstance(timeout, httpx.Timeout) else timeout
    return None if seconds is None else time.monotonic() + float(seconds)
