import pytest
from app.evaluation.retrieval_benchmark import (
    BENCHMARK_QUERIES,
    evaluate_hit_relevance,
    run_retrieval_benchmark,
)


def test_benchmark_queries_dataset_structure():
    """Verify evaluation benchmark queries dataset has at least 15-20 diverse queries."""
    assert len(BENCHMARK_QUERIES) >= 15
    for q in BENCHMARK_QUERIES:
        assert "id" in q
        assert "query" in q
        assert "target_theme" in q
        assert "target_sentiment" in q
        assert "keywords" in q
        assert len(q["keywords"]) >= 2


def test_evaluate_hit_relevance():
    """Verify relevance matching logic for benchmark hits."""
    query_spec = {
        "id": "q_test",
        "query": "taste issues",
        "target_theme": "taste/flavor",
        "target_sentiment": "negative",
        "keywords": ["taste", "flavor", "bitter"],
    }

    relevant_hit = {
        "document": "The taste was completely bitter and unpleasant.",
        "metadata": {"sentiment": "negative"},
    }
    assert evaluate_hit_relevance(relevant_hit, query_spec) is True

    irrelevant_hit = {
        "document": "Arrived in a secure brown carton box.",
        "metadata": {"sentiment": "positive"},
    }
    assert evaluate_hit_relevance(irrelevant_hit, query_spec) is False


def test_benchmark_metrics_calculation():
    """Verify that run_retrieval_benchmark returns valid Precision@K and Recall@K."""
    report = run_retrieval_benchmark(k=3)
    assert report["k"] == 3
    assert report["total_queries"] == len(BENCHMARK_QUERIES)
    assert 0.0 <= report["mean_precision@3"] <= 1.0
    assert 0.0 <= report["mean_recall@3"] <= 1.0
    assert len(report["queries"]) == len(BENCHMARK_QUERIES)
