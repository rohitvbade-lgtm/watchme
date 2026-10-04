"""fix notification_event watchlist_item_id foreign key ondelete set null

Revision ID: 004
Revises: 003
Create Date: 2026-10-04 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Find constraint name dynamically if present
        result = bind.execute(sa.text("""
            SELECT conname 
            FROM pg_constraint 
            WHERE conrelid = 'notification_event'::regclass 
              AND contype = 'f'
              AND confrelid = 'watchlist_item'::regclass
        """)).fetchall()
        for row in result:
            conname = row[0]
            op.drop_constraint(conname, 'notification_event', type_='foreignkey')
        op.create_foreign_key(
            'notification_event_watchlist_item_id_fkey',
            'notification_event',
            'watchlist_item',
            ['watchlist_item_id'],
            ['id'],
            ondelete='SET NULL'
        )
    elif bind.dialect.name == "sqlite":
        with op.batch_alter_table('notification_event') as batch_op:
            batch_op.create_foreign_key(
                'notification_event_watchlist_item_id_fkey',
                'watchlist_item',
                ['watchlist_item_id'],
                ['id'],
                ondelete='SET NULL'
            )
    else:
        op.drop_constraint('notification_event_watchlist_item_id_fkey', 'notification_event', type_='foreignkey')
        op.create_foreign_key(
            'notification_event_watchlist_item_id_fkey',
            'notification_event',
            'watchlist_item',
            ['watchlist_item_id'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        result = bind.execute(sa.text("""
            SELECT conname 
            FROM pg_constraint 
            WHERE conrelid = 'notification_event'::regclass 
              AND contype = 'f'
              AND confrelid = 'watchlist_item'::regclass
        """)).fetchall()
        for row in result:
            conname = row[0]
            op.drop_constraint(conname, 'notification_event', type_='foreignkey')
        op.create_foreign_key(
            'notification_event_watchlist_item_id_fkey',
            'notification_event',
            'watchlist_item',
            ['watchlist_item_id'],
            ['id']
        )
    elif bind.dialect.name == "sqlite":
        with op.batch_alter_table('notification_event') as batch_op:
            batch_op.create_foreign_key(
                'notification_event_watchlist_item_id_fkey',
                'watchlist_item',
                ['watchlist_item_id'],
                ['id']
            )
    else:
        op.drop_constraint('notification_event_watchlist_item_id_fkey', 'notification_event', type_='foreignkey')
        op.create_foreign_key(
            'notification_event_watchlist_item_id_fkey',
            'notification_event',
            'watchlist_item',
            ['watchlist_item_id'],
            ['id']
        )
