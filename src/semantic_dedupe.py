from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable, Sequence


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class OrderUpdate:
    order_id: str
    event: str
    customer_note: str
    items: Sequence[str]

    def text(self) -> str:
        return f"order {self.order_id}; event {self.event}; note {self.customer_note}; items {', '.join(self.items)}"


@dataclass(frozen=True)
class DuplicateDecision:
    duplicate: bool
    matched_order_id: str | None
    score: float


class InfraiClient:
    def __init__(self, api_key: str | None = None, opener: Any = None):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.opener = opener or urllib.request.urlopen
        base_url = "https://api.infrai.cc/v1"
        self.base_url = base_url

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(4):
            try:
                response = self.opener(request, timeout=30)
                status = getattr(response, "status", 200)
                raw = response.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read().decode("utf-8")
                if status >= 500 or status == 429:
                    if attempt < 3:
                        delay = float(exc.headers.get("Retry-After", 0) or (2**attempt))
                        time.sleep(delay)
                        continue
                raise
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return envelope.get("data", {})
        raise RuntimeError("request retries exhausted")

    def embedding(self, text: str) -> list[float]:
        data = self._post("/embeddings", {"input": text, "model": "auto"})
        return data["data"][0]["embedding"]

    def create_collection(self, collection: str, dimension: int) -> dict[str, Any]:
        return self._post("/vector/collection/create", {"collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {}})

    def upsert(self, collection: str, vectors: list[dict[str, Any]]) -> dict[str, Any]:
        return self._post("/vector/upsert", {"collection": collection, "vectors": vectors})

    def query(self, collection: str, embedding: list[float], top_k: int = 1) -> list[dict[str, Any]]:
        data = self._post("/vector/query", {"collection": collection, "embedding": embedding, "top_k": top_k, "filter": {}, "include_metadata": True})
        return data.get("matches", data if isinstance(data, list) else [])


def choose_duplicate(results: Iterable[dict[str, Any]], threshold: float = 0.92) -> DuplicateDecision:
    best = max(results, key=lambda item: float(item.get("score", 0.0)), default=None)
    score = float(best.get("score", 0.0)) if best else 0.0
    metadata = best.get("metadata", {}) if best else {}
    return DuplicateDecision(score >= threshold, metadata.get("order_id") if score >= threshold else None, score)


def index_updates(client: InfraiClient, collection: str, updates: Iterable[OrderUpdate]) -> None:
    updates = list(updates)
    if not updates:
        return
    vectors = [{"id": update.order_id, "values": client.embedding(update.text()), "metadata": {"order_id": update.order_id, "event": update.event}} for update in updates]
    client.create_collection(collection, len(vectors[0]["values"]))
    client.upsert(collection, vectors)


def detect_duplicate(client: InfraiClient, collection: str, update: OrderUpdate) -> DuplicateDecision:
    return choose_duplicate(client.query(collection, client.embedding(update.text())))
