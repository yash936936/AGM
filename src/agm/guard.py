"""Input guardrails: redact secrets before persistence/embedding and quarantine injection-like text."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .models import Ctx, WriteItem, WriteResult

# The labelled rule handles common developer mistakes such as api_key=... and
# password: .... Dedicated token patterns cover formats commonly copied into logs.
_LABELLED_SECRET = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|"
    r"secret|password|passwd|authorization)\b(\s*[:=]\s*)([\"']?)([^\s,;\"']{8,})([\"']?)"
)
_BEARER_SECRET = re.compile(r"(?i)\b(bearer)\s+([A-Za-z0-9._~+/=-]{12,})")
_TOKEN_PATTERNS = [
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|sk_(?:live|test)_[A-Za-z0-9]{12,})\b"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}\b"),
]
_INSTRUCTION_PATTERNS = [
    re.compile(r"\bignore\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|above)\s+instructions?\b", re.I),
    re.compile(r"\bdisregard\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|above)\s+instructions?\b", re.I),
    re.compile(r"\b(?:reveal|print|expose|leak)\s+(?:the\s+)?(?:system|hidden|developer)\s+prompt\b", re.I),
    re.compile(r"\byou\s+must\s+now\s+(?:ignore|override|reveal|expose)\b", re.I),
    re.compile(r"\boverride\s+(?:the\s+)?(?:system|safety)\s+(?:prompt|rules|instructions)\b", re.I),
]


@dataclass(frozen=True)
class GuardedWrite:
    item: WriteItem
    redactions: int
    quarantine_reasons: tuple[str, ...]


def _redact_text(value: str) -> tuple[str, int]:
    count = 0

    def labelled(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return f"{match.group(1)}{match.group(2)}{match.group(3)}[REDACTED]{match.group(5)}"

    result = _LABELLED_SECRET.sub(labelled, value)

    def bearer(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return f"{match.group(1)} [REDACTED]"

    result = _BEARER_SECRET.sub(bearer, result)
    for pattern in _TOKEN_PATTERNS:
        def token_replacer(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return "[REDACTED]"
        result = pattern.sub(token_replacer, result)
    return result, count


def inspect_write_item(item: WriteItem) -> GuardedWrite:
    """Return a sanitized copy. All string fields are sanitized before event append and embedding."""
    redactions = 0

    def sanitize(value: Any) -> Any:
        nonlocal redactions
        if isinstance(value, str):
            clean, count = _redact_text(value)
            redactions += count
            return clean
        if isinstance(value, list):
            return [sanitize(child) for child in value]
        if isinstance(value, dict):
            return {key: sanitize(child) for key, child in value.items()}
        return value

    safe_data = sanitize(item.model_dump(mode="json"))
    safe_item = WriteItem.model_validate(safe_data)
    def collect_strings(value: Any) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [part for child in value for part in collect_strings(child)]
        if isinstance(value, dict):
            return [part for child in value.values() for part in collect_strings(child)]
        return []

    combined = " ".join(collect_strings(safe_item.model_dump(mode="json")))
    reasons = tuple(
        f"Instruction-like text matched guard rule {index + 1}."
        for index, pattern in enumerate(_INSTRUCTION_PATTERNS)
        if pattern.search(combined)
    )
    return GuardedWrite(item=safe_item, redactions=redactions, quarantine_reasons=reasons)


def guarded_write(store: Any, ctx: Ctx, item: WriteItem) -> WriteResult:
    """Guard a write shared by the REST and MCP adapters."""
    guarded = inspect_write_item(item)
    warnings: list[str] = []
    if guarded.redactions:
        warnings.append("Secrets were redacted before the event was stored and embedded.")
    warnings.extend(guarded.quarantine_reasons)
    if guarded.quarantine_reasons:
        warnings.insert(0, "Candidate was quarantined and excluded from default retrieval.")
        result = store.write_quarantined(
            ctx, guarded.item, redactions=guarded.redactions, warnings=warnings,
        )
        return result
    result = store.write(ctx, guarded.item)
    return result.model_copy(update={"redactions": guarded.redactions, "warnings": warnings + result.warnings})
