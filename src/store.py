from __future__ import annotations

import os
from typing import Any, Callable

from .chunking import compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            persist_dir = os.getenv("CHROMA_PERSIST_DIR")
            client = (
                chromadb.PersistentClient(path=persist_dir)
                if persist_dir
                else chromadb.EphemeralClient()
            )
            self._collection = client.get_or_create_collection(name=collection_name)
            # Chỉ bật cờ SAU KHI collection thực sự tạo được.
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Chuẩn hóa một Document thành record lưu trong store (kèm vector đã nhúng)."""
        metadata = dict(doc.metadata or {})
        # Quan trọng: doc không có metadata['doc_id'] thì lấy chính id của doc,
        # nếu không delete_document() và lọc theo doc_id sẽ không bao giờ khớp.
        metadata.setdefault("doc_id", doc.id)
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Xếp hạng `records` theo độ tương tự với `query`, trả top_k (giảm dần)."""
        if not records or top_k <= 0:
            return []

        query_vector = self._embedding_fn(query)
        scored = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": compute_similarity(query_vector, record["embedding"]),
            }
            for record in records
        ]
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]
        self._store.extend(records)
        self._next_index += len(records)

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[r["id"] for r in records],
                    documents=[r["content"] for r in records],
                    embeddings=[r["embedding"] for r in records],
                    metadatas=[r["metadata"] for r in records],
                )
            except Exception:
                # Chroma lỗi thì vẫn còn bản in-memory làm nguồn sự thật.
                self._use_chroma = False

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            candidates = self._store
        else:
            candidates = [
                record
                for record in self._store
                if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
            ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        removed_ids = [r["id"] for r in self._store if r["metadata"].get("doc_id") == doc_id]
        if not removed_ids:
            return False

        self._store = [r for r in self._store if r["metadata"].get("doc_id") != doc_id]

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=removed_ids)
            except Exception:
                self._use_chroma = False
        return True
