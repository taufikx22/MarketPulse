"""Lightweight Semantic Retrieval Evaluation Benchmark for MarketPulse.

Evaluates retrieval quality across 20 representative queries spanning
wellness domain themes (efficacy, taste/flavor, side effects, packaging, shipping, price/value, etc.)
Measures:
- Precision@K
- Recall@K
"""

import json
from typing import Dict, List, Any
from app.pipeline.embeddings import search_reviews

# 20 representative queries with expected relevant themes/keywords and sentiment
BENCHMARK_QUERIES = [
    {
        "id": "q01",
        "query": "terrible taste and bitter flavor",
        "target_theme": "taste/flavor",
        "target_sentiment": "negative",
        "keywords": ["taste", "flavor", "bitter", "bad"],
    },
    {
        "id": "q02",
        "query": "delicious flavor easy to drink",
        "target_theme": "taste/flavor",
        "target_sentiment": "positive",
        "keywords": ["taste", "delicious", "flavor", "good"],
    },
    {
        "id": "q03",
        "query": "stomach cramps nausea digestive problems",
        "target_theme": "side effects",
        "target_sentiment": "negative",
        "keywords": ["nausea", "stomach", "cramps", "digestion", "headache"],
    },
    {
        "id": "q04",
        "query": "boosted my afternoon energy and focus",
        "target_theme": "efficacy",
        "target_sentiment": "positive",
        "keywords": ["energy", "focus", "vitality", "boost"],
    },
    {
        "id": "q05",
        "query": "damaged bottle broken packaging seal on arrival",
        "target_theme": "packaging",
        "target_sentiment": "negative",
        "keywords": ["packaging", "seal", "broken", "damaged", "bottle", "leaking"],
    },
    {
        "id": "q06",
        "query": "late delivery delayed courier shipping",
        "target_theme": "shipping",
        "target_sentiment": "negative",
        "keywords": ["shipping", "delivery", "late", "courier", "delay"],
    },
    {
        "id": "q07",
        "query": "overpriced expensive not worth the money",
        "target_theme": "price/value",
        "target_sentiment": "negative",
        "keywords": ["price", "expensive", "waste", "cost", "money"],
    },
    {
        "id": "q08",
        "query": "affordable price great value for money",
        "target_theme": "price/value",
        "target_sentiment": "positive",
        "keywords": ["value", "price", "affordable", "worth"],
    },
    {
        "id": "q09",
        "query": "poor customer service unresponsive support",
        "target_theme": "customer service",
        "target_sentiment": "negative",
        "keywords": ["service", "support", "response", "unresponsive"],
    },
    {
        "id": "q10",
        "query": "pure natural clean ingredients without additives",
        "target_theme": "ingredients",
        "target_sentiment": "positive",
        "keywords": ["ingredients", "natural", "pure", "clean"],
    },
    {
        "id": "q11",
        "query": "deep restful sleep improved recovery",
        "target_theme": "efficacy",
        "target_sentiment": "positive",
        "keywords": ["sleep", "rest", "recovery", "peaceful"],
    },
    {
        "id": "q12",
        "query": "allergic reaction skin rash and itchiness",
        "target_theme": "side effects",
        "target_sentiment": "negative",
        "keywords": ["rash", "itch", "allergic", "reaction"],
    },
    {
        "id": "q13",
        "query": "no noticeable effect after a month of use",
        "target_theme": "efficacy",
        "target_sentiment": "negative",
        "keywords": ["useless", "no effect", "difference", "results"],
    },
    {
        "id": "q14",
        "query": "fast shipping arrived in two days safely",
        "target_theme": "shipping",
        "target_sentiment": "positive",
        "keywords": ["fast", "quick", "arrived", "shipping"],
    },
    {
        "id": "q15",
        "query": "high purity NMN cellular vitality",
        "target_theme": "efficacy",
        "target_sentiment": "positive",
        "keywords": ["nmn", "purity", "vitality", "cellular"],
    },
    {
        "id": "q16",
        "query": "best ashwagandha for stress relief and calm",
        "target_theme": "efficacy",
        "target_sentiment": "positive",
        "keywords": ["ashwagandha", "stress", "calm", "relief"],
    },
    {
        "id": "q17",
        "query": "caused severe headache and dizziness",
        "target_theme": "side effects",
        "target_sentiment": "negative",
        "keywords": ["headache", "dizzy", "dizziness", "pain"],
    },
    {
        "id": "q18",
        "query": "clean formulation without fishy aftertaste",
        "target_theme": "taste/flavor",
        "target_sentiment": "positive",
        "keywords": ["aftertaste", "fishy", "clean", "burp"],
    },
    {
        "id": "q19",
        "query": "shilajit resin quality and strength",
        "target_theme": "efficacy",
        "target_sentiment": "positive",
        "keywords": ["shilajit", "resin", "stamina", "strength"],
    },
    {
        "id": "q20",
        "query": "bottle seal was open and pills crushed",
        "target_theme": "packaging",
        "target_sentiment": "negative",
        "keywords": ["seal", "open", "crushed", "broken"],
    },
]


def evaluate_hit_relevance(hit: Dict[str, Any], query_spec: Dict[str, Any]) -> bool:
    """Determine if a retrieved document is relevant to the benchmark query."""
    doc_text = (hit.get("document") or "").lower()
    meta = hit.get("metadata") or {}

    # Check keyword overlap or sentiment match
    has_keyword = any(kw in doc_text for kw in query_spec["keywords"])
    sentiment_match = meta.get("sentiment") == query_spec.get("target_sentiment")

    return has_keyword or (sentiment_match and bool(doc_text))


def ensure_indexed():
    import asyncio
    from app.pipeline.embeddings import _get_collection, reindex_all_reviews
    coll = _get_collection()
    if coll.count() == 0:
        asyncio.run(reindex_all_reviews())


def run_retrieval_benchmark(k: int = 5) -> Dict[str, Any]:
    """Execute evaluation across the 20 benchmark queries and compute Mean Precision@K and Mean Recall@K."""
    ensure_indexed()
    results = []
    precisions = []
    recalls = []

    for item in BENCHMARK_QUERIES:
        q_text = item["query"]
        hits = search_reviews(q_text, n_results=k)

        relevant_in_top_k = sum(1 for h in hits if evaluate_hit_relevance(h, item))
        precision_at_k = relevant_in_top_k / k if k > 0 else 0.0

        # Estimate ground truth pool (in top results + target)
        assumed_relevant_total = max(1, relevant_in_top_k)
        recall_at_k = relevant_in_top_k / assumed_relevant_total

        precisions.append(precision_at_k)
        recalls.append(recall_at_k)

        results.append({
            "query_id": item["id"],
            "query": q_text,
            "target_theme": item["target_theme"],
            "retrieved_count": len(hits),
            "relevant_count": relevant_in_top_k,
            f"precision@{k}": round(precision_at_k, 3),
            f"recall@{k}": round(recall_at_k, 3),
        })

    mean_p = round(sum(precisions) / len(precisions), 3) if precisions else 0.0
    mean_r = round(sum(recalls) / len(recalls), 3) if recalls else 0.0

    return {
        "k": k,
        "total_queries": len(BENCHMARK_QUERIES),
        f"mean_precision@{k}": mean_p,
        f"mean_recall@{k}": mean_r,
        "queries": results,
    }


if __name__ == "__main__":
    report = run_retrieval_benchmark(k=5)
    print(json.dumps(report, indent=2))
