"""Generate and store review embeddings in ChromaDB for semantic search."""

import chromadb
from typing import Optional
from app.config import get_settings

_collection = None


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection

    settings = get_settings()
    try:
        client = chromadb.HttpClient(host=settings.chromadb_host, port=settings.chromadb_port)
    except Exception:
        client = chromadb.Client()  # in-memory fallback

    # Use a lightweight MockEmbeddingFunction for offline dev to avoid heavy ONNX model downloads
    class MockEmbeddingFunction(chromadb.EmbeddingFunction):
        def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
            embeddings = []
            for text in input:
                # Deterministic float vector based on simple character sum
                val = float(sum(ord(c) for c in text) % 100) / 100.0
                embeddings.append([val] * 384)
            return embeddings

    _collection = client.get_or_create_collection("reviews", embedding_function=MockEmbeddingFunction())

    return _collection


def upsert_review(review_id: int, text: str, metadata: Optional[dict] = None):
    collection = _get_collection()
    doc_id = f"review_{review_id}"
    meta = metadata or {}
    meta["review_id"] = review_id
    collection.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[meta],
    )
    return doc_id


def search_reviews(query: str, n_results: int = 10, where: Optional[dict] = None) -> list[dict]:
    collection = _get_collection()
    kwargs = {"query_texts": [query], "n_results": n_results}
    if where:
        kwargs["where"] = where
    results = collection.query(**kwargs)

    hits = []
    if results and results["ids"]:
        for i, doc_id in enumerate(results["ids"][0]):
            hit = {
                "id": doc_id,
                "document": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None,
            }
            hits.append(hit)
    return hits


def batch_upsert(reviews: list[dict]):
    """reviews: list of {"review_id": int, "text": str, "metadata": dict}"""
    collection = _get_collection()
    ids = [f"review_{r['review_id']}" for r in reviews]
    docs = [r["text"] for r in reviews]
    metas = [{"review_id": r["review_id"], **r.get("metadata", {})} for r in reviews]
    collection.upsert(ids=ids, documents=docs, metadatas=metas)
