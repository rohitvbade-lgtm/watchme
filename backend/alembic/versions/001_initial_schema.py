"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-10-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('media_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('provider_id', sa.String(), nullable=False),
        sa.Column('media_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('original_title', sa.String(), nullable=True),
        sa.Column('overview', sa.String(), nullable=True),
        sa.Column('poster_path', sa.String(), nullable=True),
        sa.Column('backdrop_path', sa.String(), nullable=True),
        sa.Column('release_date', sa.Date(), nullable=True),
        sa.Column('first_air_date', sa.Date(), nullable=True),
        sa.Column('runtime', sa.Integer(), nullable=True),
        sa.Column('genres_json', sa.JSON(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('vote_count', sa.Integer(), nullable=True),
        sa.Column('popularity', sa.Float(), nullable=True),
        sa.Column('original_language', sa.String(), nullable=True),
        sa.Column('adult', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_id', 'media_type', name='uq_media_item_provider_id_type')
    )
    
    op.create_table('device',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('push_token', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id')
    )
    
    op.create_table('watchlist_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('media_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('watched', sa.Boolean(), nullable=True),
        sa.Column('watched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['media_item_id'], ['media_item.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id', 'media_item_id', name='uq_watchlist_item_device_media')
    )

    op.create_table('notification_event',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('watchlist_item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('generation_method', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['watchlist_item_id'], ['watchlist_item.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('notification_event')
    op.drop_table('watchlist_item')
    op.drop_table('device')
    op.drop_table('media_item')
