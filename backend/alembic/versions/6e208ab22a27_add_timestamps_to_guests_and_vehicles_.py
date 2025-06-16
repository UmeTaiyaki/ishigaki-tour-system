"""Add timestamps to guests and vehicles tables

Revision ID: [自動生成されたID]
Revises: 3f1ef5f4b7ac
Create Date: [自動生成された日時]

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '[自動生成されたID]'
down_revision: Union[str, None] = '3f1ef5f4b7ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # guestsテーブルにタイムスタンプを追加
    op.add_column('guests', sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True))
    op.add_column('guests', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True))
    
    # vehiclesテーブルにタイムスタンプを追加
    op.add_column('vehicles', sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True))
    op.add_column('vehicles', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True))
    
    # トリガー関数が存在しない場合は作成
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # guestsテーブルのトリガーを作成
    op.execute("""
        DROP TRIGGER IF EXISTS update_guests_updated_at ON guests;
        CREATE TRIGGER update_guests_updated_at BEFORE UPDATE ON guests
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # vehiclesテーブルのトリガーを作成
    op.execute("""
        DROP TRIGGER IF EXISTS update_vehicles_updated_at ON vehicles;
        CREATE TRIGGER update_vehicles_updated_at BEFORE UPDATE ON vehicles
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # トリガーを削除
    op.execute("DROP TRIGGER IF EXISTS update_guests_updated_at ON guests;")
    op.execute("DROP TRIGGER IF EXISTS update_vehicles_updated_at ON vehicles;")
    
    # カラムを削除
    op.drop_column('vehicles', 'updated_at')
    op.drop_column('vehicles', 'created_at')
    op.drop_column('guests', 'updated_at')
    op.drop_column('guests', 'created_at')