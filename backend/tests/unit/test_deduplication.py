import pytest
from sqlalchemy.exc import IntegrityError
from app.pipeline.cleaning import make_review_hash, clean_review
from app.models.review import Review


def test_identical_normalized_reviews_generate_identical_hashes():
    text1 = "Great supplement, noticeably increased my afternoon energy levels."
    text2 = "  Great   supplement, noticeably increased my afternoon energy levels.  "
    product_id = 10

    hash1 = make_review_hash(text1, product_id)
    hash2 = make_review_hash(text2, product_id)
    assert hash1 == hash2


def test_different_products_produce_different_hashes():
    text = "Great supplement, noticeably increased my afternoon energy levels."
    hash_prod1 = make_review_hash(text, product_id=1)
    hash_prod2 = make_review_hash(text, product_id=2)
    assert hash_prod1 != hash_prod2


def test_different_texts_produce_different_hashes():
    hash1 = make_review_hash("Great product for focus", product_id=1)
    hash2 = make_review_hash("Bad product, caused headaches", product_id=1)
    assert hash1 != hash2


@pytest.mark.asyncio
async def test_duplicate_insertion_prevented(db_session, seeded_session):
    """Test database unique constraint on text_hash prevents duplicate insertion."""
    data = seeded_session
    product = data["products"][0]

    # Attempt to insert a review with a text_hash that already exists
    duplicate_review = Review(
        product_id=product.id,
        author="Impostor",
        rating=5,
        raw_text="Incredible energy boost and vitality after 2 weeks of use!",
        text_hash="hash_alice_1",  # Same as r1 seeded in conftest
    )
    db_session.add(duplicate_review)

    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()
