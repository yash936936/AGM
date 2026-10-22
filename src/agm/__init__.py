"""Adaptive Graph Memory, Phase 2 graph-aware prototype."""

from .models import Ctx, DeleteResult, Relation, RetrieveResult, SourceSpan, WriteItem, WriteResult
from .store import MemoryStore

__all__ = [
    "Ctx", "DeleteResult", "MemoryStore", "Relation", "RetrieveResult",
    "SourceSpan", "WriteItem", "WriteResult",
]
__version__ = "0.2.0"
