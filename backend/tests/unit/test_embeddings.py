import pytest
import numpy as np
from app.pipeline.embeddings import (
    get_embedding_model,
    RealSentenceTransformerEmbeddingFunction,
    upsert_review,
    search_reviews,
    batch_upsert,
    MODEL_NAME,
    EMBEDDING_DIM,
)


def test_embedding_model_singleton():
    """Verify that get_embedding_model returns the singleton SentenceTransformer instance."""
    model1 = get_embedding_model()
    model2 = get_embedding_model()
    assert model1 is model2
    assert model1 is not None


def test_embedding_generation_and_dimensionality():
    """Verify real embeddings are 384-dimensional and normalized to unit length."""
    model = get_embedding_model()
    text = "Great wellness supplement, boosted my stamina."
    vector = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    assert isinstance(vector, np.ndarray)
    assert vector.shape == (EMBEDDING_DIM,)
    assert round(float(np.linalg.norm(vector)), 3) == 1.0


def test_embedding_function_call():
    """Test RealSentenceTransformerEmbeddingFunction meets ChromaDB EmbeddingFunction protocol."""
    fn = RealSentenceTransformerEmbeddingFunction()
    docs = ["First review text", "Second review text about taste"]
    embeddings = fn(docs)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == EMBEDDING_DIM
    assert len(embeddings[1]) == EMBEDDING_DIM
    assert fn.name() == f"sentence-transformers/{MODEL_NAME}"


def test_chromadb_upsert_and_semantic_search():
    """Test upserting reviews into ChromaDB and retrieving them with semantic search."""
    # Insert two distinct reviews
    upsert_review(
        review_id=901,
        text="The taste is absolutely delicious and refreshing watermelon flavor.",
        metadata={"brand_id": 99, "sentiment": "positive", "rating": 5},
    )
    upsert_review(
        review_id=902,
        text="Severe stomach cramps and nausea after taking two capsules.",
        metadata={"brand_id": 99, "sentiment": "negative", "rating": 1},
    )

    # Search for digestive issues
    hits_stomach = search_reviews("digestive discomfort and stomach ache", n_results=2)
    assert len(hits_stomach) > 0
    top_hit = hits_stomach[0]
    assert top_hit["metadata"]["review_id"] == 902
    assert top_hit["metadata"]["sentiment"] == "negative"
    assert "distance" in top_hit
    assert "relevance" in top_hit
    assert 0.0 <= top_hit["relevance"] <= 1.0


def test_chromadb_metadata_filtering():
    """Verify filtering by sentiment and brand_id in ChromaDB."""
    upsert_review(
        review_id=903,
        text="Affordable multivitamin supplement for daily health.",
        metadata={"brand_id": 77, "sentiment": "positive", "rating": 5},
    )
    upsert_review(
        review_id=904,
        text="Overpriced multivitamin, poor packaging seal.",
        metadata={"brand_id": 77, "sentiment": "negative", "rating": 2},
    )

    # Filter by sentiment == negative
    negative_hits = search_reviews(
        "multivitamin",
        n_results=5,
        where={"sentiment": "negative"},
    )
    assert all(h["metadata"]["sentiment"] == "negative" for h in negative_hits)
    neg_ids = [h["metadata"]["review_id"] for h in negative_hits]
    assert 904 in neg_ids
    assert 903 not in neg_ids
