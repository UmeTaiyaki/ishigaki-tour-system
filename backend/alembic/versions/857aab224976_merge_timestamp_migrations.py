"""Merge timestamp migrations

Revision ID: 857aab224976
Revises: [自動生成されたID], db4ab1a42740
Create Date: 2025-06-16 19:58:46.080293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '857aab224976'
down_revision: Union[str, None] = ('[自動生成されたID]', 'db4ab1a42740')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
