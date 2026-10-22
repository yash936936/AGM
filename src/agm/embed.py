"""Deterministic dependency-light feature hashing embeddings."""
from __future__ import annotations

from typing import Protocol
import hashlib
import numpy as np


class Embedder(Protocol):
    model_id: str

    def embed(self, text: str) -> np.ndarray: ...


class HashEmbedder:
    model_id = "hash-256-v1"
    dim = 256

    def embed(self, text: str) -> np.ndarray:
        normalized = f" {text.lower()} "
        grams = [normalized[i:i + 3] for i in range(max(0, len(normalized) - 2))]
        vector = np.zeros(self.dim, dtype=np.float32)
        for gram in grams:
            digest = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
            number = int.from_bytes(digest, "little", signed=False)
            index = number % self.dim
            sign = 1.0 if (number >> 8) & 1 else -1.0
            vector[index] += sign
        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector /= np.float32(norm)
        return vector.astype(np.float32, copy=False)
