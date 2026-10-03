"""add item_title and item_image_url to notification_event

Revision ID: 002
Revises: 001
Create Date: 2026-10-03 23:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('notification_event', sa.Column('item_title', sa.String(), nullable=True))
    op.add_column('notification_event', sa.Column('item_image_url', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('notification_event', 'item_image_url')
    op.drop_column('notification_event', 'item_title')
