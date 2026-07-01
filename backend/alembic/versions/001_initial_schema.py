"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-07-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('brands',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('url', sa.String(512), nullable=False),
        sa.Column('category', sa.String(100), server_default='wellness'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('products',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('brand_id', sa.Integer(), sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(512), nullable=False),
        sa.Column('url', sa.String(1024), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(1024), nullable=True),
        sa.Column('last_scraped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('reviews',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('cleaned_text', sa.Text(), nullable=True),
        sa.Column('rating', sa.SmallInteger(), nullable=True),
        sa.Column('author', sa.String(255), nullable=True),
        sa.Column('review_date', sa.Date(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('text_hash', sa.String(64), unique=True, nullable=False),
    )

    op.create_table('review_analysis',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('review_id', sa.Integer(), sa.ForeignKey('reviews.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('sentiment', sa.String(20), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('themes', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('embedding_id', sa.String(255), nullable=True),
    )

    op.create_table('insights',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('brand_id', sa.Integer(), sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('supporting_review_ids', sa.ARRAY(sa.Integer()), nullable=True),
    )

    op.create_table('organizations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('clerk_org_id', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('clerk_user_id', sa.String(255), unique=True, nullable=False),
        sa.Column('email', sa.String(320), nullable=False),
        sa.Column('name', sa.String(255), server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('org_memberships',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('org_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), server_default='viewer'),
    )

    op.create_table('watchlists',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('org_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('brand_id', sa.Integer(), sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('org_id', 'brand_id', name='uq_watchlist_org_brand'),
    )


def downgrade() -> None:
    op.drop_table('watchlists')
    op.drop_table('org_memberships')
    op.drop_table('users')
    op.drop_table('organizations')
    op.drop_table('insights')
    op.drop_table('review_analysis')
    op.drop_table('reviews')
    op.drop_table('products')
    op.drop_table('brands')
