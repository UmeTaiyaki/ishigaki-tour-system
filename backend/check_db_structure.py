"""
データベースのテーブル構造を確認
"""

from sqlalchemy import create_engine, inspect
from app.core.config import settings

def check_database_structure():
    """データベースの構造を確認"""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    # テーブル一覧
    tables = inspector.get_table_names()
    print("=== データベーステーブル一覧 ===")
    for table in tables:
        print(f"\n📋 テーブル: {table}")
        
        # カラム情報
        columns = inspector.get_columns(table)
        print("  カラム:")
        for col in columns:
            print(f"    - {col['name']}: {col['type']} {'(NOT NULL)' if not col['nullable'] else ''}")
        
        # インデックス
        indexes = inspector.get_indexes(table)
        if indexes:
            print("  インデックス:")
            for idx in indexes:
                print(f"    - {idx['name']}: {idx['column_names']}")
        
        # 外部キー
        foreign_keys = inspector.get_foreign_keys(table)
        if foreign_keys:
            print("  外部キー:")
            for fk in foreign_keys:
                print(f"    - {fk['name']}: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

if __name__ == "__main__":
    check_database_structure()