from __future__ import annotations

import re
from dataclasses import dataclass

from devticket_agent.io_utils import load_json


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+")


@dataclass(frozen=True)
class RetrievedDocument:
    id: str
    title: str
    content: str
    score: float


def tokenize(text: str) -> set[str]:
    tokens: set[str] = set()
    for token in TOKEN_PATTERN.findall(text):
        normalized = token.lower()
        if re.fullmatch(r"[\u4e00-\u9fff]+", normalized):
            tokens.update(normalized[index : index + 2] for index in range(max(len(normalized) - 1, 1)))
        else:
            tokens.add(normalized)
    return tokens


class KeywordRetriever:
    def __init__(self, data_path: str = "data/knowledge_base.json") -> None:
        self.documents = load_json(data_path)
        self._cache: dict[tuple[str, int], list[RetrievedDocument]] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def search(self, query: str, top_k: int = 3) -> list[RetrievedDocument]:
        cache_key = (query, top_k)
        if cache_key in self._cache:
            self.cache_hits += 1
            return self._cache[cache_key]

        self.cache_misses += 1
        query_tokens = tokenize(query)
        ranked: list[RetrievedDocument] = []

        for doc in self.documents:
            doc_text = f"{doc['title']} {doc['content']}"
            doc_tokens = tokenize(doc_text)
            overlap = query_tokens & doc_tokens
            score = len(overlap) / max(len(query_tokens), 1)
            for token in query_tokens:
                if len(token) >= 4 and token in doc_text.lower():
                    score += 0.2
            if score > 0:
                ranked.append(
                    RetrievedDocument(
                        id=doc["id"],
                        title=doc["title"],
                        content=doc["content"],
                        score=round(score, 3),
                    )
                )

        results = sorted(ranked, key=lambda item: item.score, reverse=True)[:top_k]
        self._cache[cache_key] = results
        return results
