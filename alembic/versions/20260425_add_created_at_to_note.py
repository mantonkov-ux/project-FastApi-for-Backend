"""add created_at to note

Revision ID: b7420f11d99f
Revises: 6c8f85c2d9e6
Create Date: 2026-04-25 16:10:51.195510

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7420f11d99f'
down_revision: Union[str, Sequence[str], None] = '6c8f85c2d9e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Добавляем колонку created_at
    op.add_column(
        'note',
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True)
    )
    # Обновляем старые записи — ставим текущее время
    op.execute("UPDATE note SET created_at = CURRENT_TIMESTAMP")

def downgrade() -> None:
    # Удаляем колонку при откате
    op.drop_column('note', 'created_at')
