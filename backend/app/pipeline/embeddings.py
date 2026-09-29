"""Generate and store review embeddings in ChromaDB using sentence-transformers for semantic search."""

import logging
from typing import Optional, List, Dict, Any
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database import async_session

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_collection = None
_embedding_model = None
_embedding_function = None


def get_embedding_model():
    """Load the sentence-transformers model once as a singleton."""
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model

    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformer embedding model: %s...", MODEL_NAME)
        try:
            _embedding_model = SentenceTransformer(MODEL_NAME, local_files_only=True)
        except Exception:
            _embedding_model = SentenceTransformer(MODEL_NAME)
        logger.info("Loaded sentence-transformer model: %s (dimension: %d)", MODEL_NAME, EMBEDDING_DIM)
        return _embedding_model
    except Exception as exc:
        logger.error("Failed to load sentence-transformer model '%s': %s", MODEL_NAME, exc)
        raise RuntimeError(
            f"Failed to initialize embedding model '{MODEL_NAME}'. "
            f"Ensure sentence-transformers is installed and weights are accessible: {exc}"
        ) from exc


class RealSentenceTransformerEmbeddingFunction(EmbeddingFunction[Documents]):
    """ChromaDB-compatible embedding function backed by sentence-transformers."""

    def __init__(self, model=None):
        self._model = model

    def _get_model(self):
        if self._model is None:
            self._model = get_embedding_model()
        return self._model

    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []
        model = self._get_model()
        # Encode documents with L2 normalization for accurate cosine similarity
        embeddings = model.encode(
            list(input),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def name(self) -> str:
        return f"sentence-transformers/{MODEL_NAME}"


def _get_collection():
    """Obtain or initialize the ChromaDB 'reviews' collection."""
    global _collection, _embedding_function
    if _collection is not None:
        return _collection

    settings = get_settings()
    client = None
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            if s.connect_ex((settings.chromadb_host, int(settings.chromadb_port))) == 0:
                client = chromadb.HttpClient(host=settings.chromadb_host, port=settings.chromadb_port)
                client.heartbeat()
                logger.info("Connected to remote ChromaDB at %s:%s", settings.chromadb_host, settings.chromadb_port)
    except Exception as exc:
        logger.warning(
            "Could not connect to ChromaDB server (%s:%s); using local in-memory Chroma client: %s",
            settings.chromadb_host,
            settings.chromadb_port,
            exc,
        )

    if client is None:
        client = chromadb.Client(chromadb.config.Settings(anonymized_telemetry=False, is_persistent=False))

    if _embedding_function is None:
        _embedding_function = RealSentenceTransformerEmbeddingFunction()

    # Configure cosine distance space so distance d = 1 - cos(theta) in [0, 2]
    _collection = client.get_or_create_collection(
        name="reviews",
        embedding_function=_embedding_function,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def set_test_embedding_function(fn: EmbeddingFunction):
    """Allows test fixtures to inject an isolated embedding function for fast unit testing."""
    global _embedding_function, _collection
    _embedding_function = fn
    _collection = None


def upsert_review(review_id: int, text: str, metadata: Optional[dict] = None) -> str:
    """Upsert a single review document into ChromaDB."""
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


def batch_upsert(reviews: List[Dict[str, Any]]):
    """Batch-upsert reviews: list of {'review_id': int, 'text': str, 'metadata': dict}."""
    if not reviews:
        return
    collection = _get_collection()
    ids = [f"review_{r['review_id']}" for r in reviews]
    docs = [r["text"] for r in reviews]
    metas = [{"review_id": r["review_id"], **r.get("metadata", {})} for r in reviews]
    collection.upsert(ids=ids, documents=docs, metadatas=metas)


def search_reviews(query: str, n_results: int = 10, where: Optional[dict] = None) -> list[dict]:
    """Search for relevant reviews using cosine similarity in ChromaDB."""
    collection = _get_collection()
    kwargs = {"query_texts": [query], "n_results": n_results}
    if where:
        kwargs["where"] = where
    results = collection.query(**kwargs)

    hits = []
    if results and results["ids"] and len(results["ids"][0]) > 0:
        for i, doc_id in enumerate(results["ids"][0]):
            raw_dist = results["distances"][0][i] if results.get("distances") and len(results["distances"]) > 0 else None
            # In cosine space, similarity = max(0, 1 - distance)
            if raw_dist is not None:
                # Clamp cosine distance to [0.0, 1.0] for display consistency
                clamped_dist = round(max(0.0, min(1.0, float(raw_dist))), 4)
                relevance = round(max(0.0, min(1.0, 1.0 - clamped_dist)), 4)
            else:
                clamped_dist = 0.5
                relevance = 0.5

            hit = {
                "id": doc_id,
                "document": results["documents"][0][i] if results.get("documents") else "",
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                "distance": clamped_dist,
                "relevance": relevance,
            }
            hits.append(hit)
    return hits


async def reindex_all_reviews(session: Optional[AsyncSession] = None) -> int:
    """Reindex all reviews and analyses from SQL into ChromaDB."""
    from app.models.review import Review
    from app.models.analysis import ReviewAnalysis

    async def _do_reindex(s: AsyncSession) -> int:
        result = await s.execute(
            select(Review)
            .options(selectinload(Review.product))
            .outerjoin(ReviewAnalysis, ReviewAnalysis.review_id == Review.id)
        )
        reviews = result.scalars().all()
        if not reviews:
            return 0

        # Also get analysis map
        analyses_res = await s.execute(select(ReviewAnalysis))
        analysis_map = {a.review_id: a for a in analyses_res.scalars().all()}

        items = []
        for r in reviews:
            a = analysis_map.get(r.id)
            sentiment_label = a.sentiment if a else "neutral"
            prod_id = r.product_id
            brand_id = r.product.brand_id if r.product else 0
            text = r.cleaned_text or r.raw_text

            items.append({
                "review_id": r.id,
                "text": text,
                "metadata": {
                    "product_id": prod_id,
                    "brand_id": brand_id,
                    "sentiment": sentiment_label,
                    "rating": r.rating or 0,
                }
            })

        batch_upsert(items)
        logger.info("Successfully reindexed %d reviews into ChromaDB.", len(items))
        return len(items)

    if session is not None:
        return await _do_reindex(session)
    else:
        async with async_session() as sess:
            return await _do_reindex(sess)
