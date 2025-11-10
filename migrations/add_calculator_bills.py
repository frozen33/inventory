"""
Migration: Add calculator bills feature
Creates tables for calculation bills and bill items with 30-day lifecycle
"""

import sqlite3
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection


def migrate():
    """Add calculator bills tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Create calculation_bills table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calculation_bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                bill_name TEXT,
                total_boxes INTEGER DEFAULT 0,
                total_price DECIMAL(10,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Create calculation_bill_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calculation_bill_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id INTEGER NOT NULL,
                product_id INTEGER NULL,
                source_type TEXT NOT NULL,
                calculation_type TEXT NOT NULL,
                tile_name TEXT NOT NULL,
                dimensions TEXT NOT NULL,
                tiles_per_box INTEGER,
                coverage_per_box DECIMAL(10,2),
                room_dimensions TEXT,
                area_calculated DECIMAL(10,2),
                boxes_exact DECIMAL(10,2),
                boxes_needed INTEGER,
                price_per_box DECIMAL(10,2) NULL,
                total_price DECIMAL(10,2) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bill_id) REFERENCES calculation_bills (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL
            )
        """)

        conn.commit()
        print("✅ Migration successful: Calculator bills tables created")

        # Verify tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('calculation_bills', 'calculation_bill_items')
        """)
        tables = cursor.fetchall()
        print(f"   Created tables: {[t[0] for t in tables]}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def rollback():
    """Remove calculator bills tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DROP TABLE IF EXISTS calculation_bill_items")
        cursor.execute("DROP TABLE IF EXISTS calculation_bills")
        conn.commit()
        print("✅ Rollback successful: Calculator bills tables removed")
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback()
    else:
        migrate()
