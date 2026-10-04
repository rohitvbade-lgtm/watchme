"""add rewatch flag to watchlist_item

Revision ID: 003
Revises: 002
Create Date: 2026-10-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'watchlist_item',
        sa.Column('rewatch', sa.Boolean(), nullable=True, server_default=sa.false())
    )


def downgrade() -> None:
    op.drop_column('watchlist_item', 'rewatch')
