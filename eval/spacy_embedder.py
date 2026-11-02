"""Eval-only embedder: mean of spaCy en_core_web_md static word vectors (300-d). Not a production dependency.

Weaker than a sentence-transformer, but a genuine semantic embedding that works offline once the model wheel is
installed (``pip install spacy`` then the en_core_web_md wheel). Used to test paraphrase handling in
eval/labelled_v3.py.
"""
from __future__ import annotations

import numpy as np


class SpacyEmbedder:
    model_id = "spacy-en_core_web_md-meanvec"
    dim = 300

    def __init__(self) -> None:
        try:
            import spacy
            self._nlp = spacy.load("en_core_web_md", disable=["tagger", "parser", "ner", "lemmatizer", "attribute_ruler"])
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("Install spaCy and en_core_web_md to use --embedder spacy.") from exc
        self._cache: dict[str, np.ndarray] = {}

    def embed(self, text: str) -> np.ndarray:
        vectors = []
        for token in self._nlp.tokenizer(text.lower()):
            if token.is_alpha or token.like_num:
                lex = self._nlp.vocab[token.text]
                if lex.has_vector:
                    vectors.append(self._cache.setdefault(token.text, np.asarray(lex.vector, dtype=np.float32)))
        if not vectors:
            return np.zeros(self.dim, dtype=np.float32)
        mean = np.mean(vectors, axis=0)
        norm = float(np.linalg.norm(mean))
        return (mean / norm).astype(np.float32) if norm > 0 else mean.astype(np.float32)
