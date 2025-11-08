#!/usr/bin/env python3
"""
Migration: Add Tiles Inventory Feature
- Add product_type field to products table
- Create tiles_details table for tile-specific information
"""

import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db_connection


def backup_database(database_path='inventory.db'):
    """Create backup before migration"""
    if not os.path.exists(database_path):
        print(f"Database {database_path} does not exist!")
        return False

    backup_path = f"{database_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        source_conn = sqlite3.connect(database_path)
        backup_conn = sqlite3.connect(backup_path)
        source_conn.backup(backup_conn)
        source_conn.close()
        backup_conn.close()

        print(f"✓ Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return False


def add_product_type_field(conn):
    """Add product_type field to products table"""
    print("\n[1/3] Adding product_type field to products table...")

    try:
        # Add product_type column with default value 'power_tools'
        conn.execute("ALTER TABLE products ADD COLUMN product_type TEXT DEFAULT 'power_tools'")

        # Create index on product_type for faster filtering
        conn.execute("CREATE INDEX idx_products_type ON products(product_type)")

        conn.commit()
        print("✓ Product type field added successfully")
        return True
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ Product type field already exists")
            return True
        else:
            print(f"✗ Error adding product type field: {e}")
            return False


def create_tiles_details_table(conn):
    """Create tiles_details table for tile-specific information"""
    print("\n[2/3] Creating tiles_details table...")

    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tiles_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER UNIQUE NOT NULL,
                tiles_per_box INTEGER,
                number_of_boxes INTEGER,
                dimension_length DECIMAL(10,2),
                dimension_width DECIMAL(10,2),
                dimension_unit TEXT DEFAULT 'feet',
                sq_feet_per_box DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        ''')

        # Create index for better performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tiles_product_id ON tiles_details(product_id)")

        conn.commit()
        print("✓ Tiles details table created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating tiles details table: {e}")
        return False


def verify_migration(conn):
    """Verify that migration was successful"""
    print("\n[3/3] Verifying migration...")

    try:
        # Check products table
        cursor = conn.execute("PRAGMA table_info(products)")
        product_columns = [row[1] for row in cursor.fetchall()]
        assert 'product_type' in product_columns, "product_type column not found in products table"
        print("✓ Products table: product_type column exists")

        # Check tiles_details table
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tiles_details'")
        assert cursor.fetchone() is not None, "tiles_details table not found"
        print("✓ Tiles details table exists")

        # Check table structure
        cursor = conn.execute("PRAGMA table_info(tiles_details)")
        tiles_columns = [row[1] for row in cursor.fetchall()]
        required_columns = ['tiles_per_box', 'number_of_boxes', 'dimension_length',
                           'dimension_width', 'dimension_unit', 'sq_feet_per_box']
        for col in required_columns:
            assert col in tiles_columns, f"{col} column not found in tiles_details table"
        print("✓ Tiles details table has all required columns")

        # Check product counts
        cursor = conn.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        print(f"✓ {product_count} products in database")

        # Check default product type
        cursor = conn.execute("SELECT COUNT(*) FROM products WHERE product_type = 'power_tools'")
        power_tools_count = cursor.fetchone()[0]
        print(f"✓ {power_tools_count} products set as 'power_tools' (default)")

        print("\n✓ Migration verification successful!")
        return True
    except AssertionError as e:
        print(f"\n✗ Verification failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Verification error: {e}")
        return False


def run_migration(database_path='inventory.db'):
    """Run the complete migration"""
    print("=" * 60)
    print("MIGRATION: Add Tiles Inventory Feature")
    print("=" * 60)

    # Check if database exists
    if not os.path.exists(database_path):
        print(f"✗ Database {database_path} does not exist!")
        return False

    # Create backup
    print("\nCreating backup...")
    if not backup_database(database_path):
        response = input("Backup failed. Continue anyway? (yes/no): ").lower()
        if response != 'yes':
            print("Migration cancelled.")
            return False

    # Connect to database
    try:
        conn = get_db_connection(database_path)
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        return False

    # Run migration steps
    try:
        success = True
        success = success and add_product_type_field(conn)
        success = success and create_tiles_details_table(conn)
        success = success and verify_migration(conn)

        if success:
            print("\n" + "=" * 60)
            print("MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Restart the application:")
            print("   python app.py")
            print("\n2. Test the new tiles inventory:")
            print("   - Navigate to dashboard")
            print("   - Switch between 'Power Tools & Others' and 'Tiles' tabs")
            print("   - Add a tile product with dimensions")
            return True
        else:
            print("\n✗ Migration failed. Check errors above.")
            print("Database backup is available if you need to restore.")
            return False

    except Exception as e:
        print(f"\n✗ Migration failed with error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Migrate database to add tiles inventory feature')
    parser.add_argument('--database', default='inventory.db', help='Path to database file')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')

    args = parser.parse_args()

    if not args.force:
        print("\nThis migration will:")
        print("  - Add product_type field to products table")
        print("  - Create tiles_details table")
        print("  - Set all existing products as 'power_tools' type")
        print("\nA backup will be created automatically.")
        response = input("\nContinue with migration? (yes/no): ").lower()
        if response != 'yes':
            print("Migration cancelled.")
            sys.exit(0)

    success = run_migration(args.database)
    sys.exit(0 if success else 1)
