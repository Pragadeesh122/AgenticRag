"""Stable hashing helpers for observability labels."""

from __future__ import annotations

import hashlib
import os

_DEFAULT_SALT = "agenticrag-dev-observability-salt"
_HASH_LEN = 16


def _salt() -> str:
    return os.getenv("OBSERVABILITY_HASH_SALT", _DEFAULT_SALT)


def stable_hash(value: str | None) -> str:
    """Return a stable, salted short hash for label-safe identifiers."""
    if not value:
        return "unknown"
    digest = hashlib.sha256(f"{_salt()}::{value}".encode("utf-8")).hexdigest()
    return digest[:_HASH_LEN]

