"""Adaptive Graph Memory: event-sourced agent memory with graph retrieval, trust, handoff and lifecycle."""

from .models import Ctx, DeleteResult, ExpiryResult, Relation, RetrieveResult, SourceSpan, WriteItem, WriteResult
from .client import AgmClient, AgmError
from .store import MemoryStore

__all__ = [
    "AgmClient", "AgmError", "Ctx", "DeleteResult", "ExpiryResult", "MemoryStore", "Relation", "RetrieveResult",
    "SourceSpan", "WriteItem", "WriteResult",
]
__version__ = "0.7.0"
