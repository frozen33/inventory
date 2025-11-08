#!/usr/bin/env python3
"""
Migration: Add Collaborative Features
- Add role field to users table
- Create product_audit_log table
- Add created_by and updated_by to products table
- Backfill existing products with creator info
"""

import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path to import database module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db_connection


def backup_database(database_path='inventory.db'):
    """Create backup before migration"""
    if not os.path.exists(database_path):
        print(f"Database {database_path} does not exist!")
        return False

    backup_path = f"{database_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        # Use SQLite backup API for safe backup
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


def check_migration_needed(conn):
    """Check if migration has already been applied"""
    cursor = conn.cursor()

    # Check if role column exists in users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'role' in columns:
        print("Migration appears to already be applied (role column exists)")
        response = input("Continue anyway? (yes/no): ").lower()
        return response == 'yes'

    return True


def add_role_to_users(conn):
    """Add role column to users table"""
    print("\n[1/5] Adding role column to users table...")

    try:
        # Add role column with default value
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")

        # Create index on role for faster queries
        conn.execute("CREATE INDEX idx_users_role ON users(role)")

        conn.commit()
        print("✓ Role column added successfully")
        return True
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ Role column already exists")
            return True
        else:
            print(f"✗ Error adding role column: {e}")
            return False


def create_audit_log_table(conn):
    """Create product_audit_log table"""
    print("\n[2/5] Creating product_audit_log table...")

    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS product_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                product_name TEXT,
                changes TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Create indexes for better query performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_product_id ON product_audit_log(product_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON product_audit_log(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON product_audit_log(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON product_audit_log(action)")

        conn.commit()
        print("✓ Audit log table created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating audit log table: {e}")
        return False


def add_creator_fields_to_products(conn):
    """Add created_by and updated_by fields to products table"""
    print("\n[3/5] Adding creator tracking fields to products table...")

    try:
        # Check if columns already exist
        cursor = conn.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'created_by' not in columns:
            conn.execute("ALTER TABLE products ADD COLUMN created_by INTEGER REFERENCES users(id)")
            print("✓ Added created_by column")
        else:
            print("✓ created_by column already exists")

        if 'updated_by' not in columns:
            conn.execute("ALTER TABLE products ADD COLUMN updated_by INTEGER REFERENCES users(id)")
            print("✓ Added updated_by column")
        else:
            print("✓ updated_by column already exists")

        # Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_products_created_by ON products(created_by)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_products_updated_by ON products(updated_by)")

        conn.commit()
        return True
    except Exception as e:
        print(f"✗ Error adding creator fields: {e}")
        return False


def backfill_creator_data(conn):
    """Backfill existing products with creator information"""
    print("\n[4/5] Backfilling creator data for existing products...")

    try:
        # For existing products, set created_by and updated_by to the user_id (original owner)
        cursor = conn.execute('''
            UPDATE products
            SET created_by = user_id,
                updated_by = user_id
            WHERE created_by IS NULL OR updated_by IS NULL
        ''')

        rows_updated = cursor.rowcount

        # Create initial audit log entries for existing products
        conn.execute('''
            INSERT INTO product_audit_log (product_id, user_id, action, product_name, timestamp)
            SELECT id, user_id, 'create', name, created_at
            FROM products
            WHERE id NOT IN (SELECT DISTINCT product_id FROM product_audit_log WHERE action = 'create' AND product_id IS NOT NULL)
        ''')

        conn.commit()
        print(f"✓ Backfilled creator data for {rows_updated} products")
        print(f"✓ Created initial audit log entries")
        return True
    except Exception as e:
        print(f"✗ Error backfilling data: {e}")
        return False


def verify_migration(conn):
    """Verify that migration was successful"""
    print("\n[5/5] Verifying migration...")

    try:
        # Check users table
        cursor = conn.execute("PRAGMA table_info(users)")
        user_columns = [row[1] for row in cursor.fetchall()]
        assert 'role' in user_columns, "role column not found in users table"
        print("✓ Users table: role column exists")

        # Check products table
        cursor = conn.execute("PRAGMA table_info(products)")
        product_columns = [row[1] for row in cursor.fetchall()]
        assert 'created_by' in product_columns, "created_by column not found"
        assert 'updated_by' in product_columns, "updated_by column not found"
        print("✓ Products table: created_by and updated_by columns exist")

        # Check audit log table
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_audit_log'")
        assert cursor.fetchone() is not None, "product_audit_log table not found"
        print("✓ Audit log table exists")

        # Check audit log entries
        cursor = conn.execute("SELECT COUNT(*) FROM product_audit_log")
        audit_count = cursor.fetchone()[0]
        print(f"✓ Audit log contains {audit_count} entries")

        # Check product counts
        cursor = conn.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        print(f"✓ {product_count} products in database")

        # Check user counts
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        print(f"✓ {user_count} users ({admin_count} admins, {user_count - admin_count} regular users)")

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
    print("MIGRATION: Add Collaborative Features")
    print("=" * 60)

    # Check if database exists
    if not os.path.exists(database_path):
        print(f"✗ Database {database_path} does not exist!")
        print("Please create the database first using: python database.py")
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

    # Check if migration needed
    if not check_migration_needed(conn):
        print("Migration cancelled.")
        conn.close()
        return False

    # Run migration steps
    try:
        success = True
        success = success and add_role_to_users(conn)
        success = success and create_audit_log_table(conn)
        success = success and add_creator_fields_to_products(conn)
        success = success and backfill_creator_data(conn)
        success = success and verify_migration(conn)

        if success:
            print("\n" + "=" * 60)
            print("MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Promote your first admin user:")
            print("   python scripts/manage_admin.py promote <email>")
            print("\n2. Start the application:")
            print("   python app.py")
            print("\n3. Test the collaborative features:")
            print("   - Login with multiple users")
            print("   - Verify all users see all products")
            print("   - Check audit logging works")
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

    parser = argparse.ArgumentParser(description='Migrate database to add collaborative features')
    parser.add_argument('--database', default='inventory.db', help='Path to database file')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')

    args = parser.parse_args()

    if not args.force:
        print("\nThis migration will:")
        print("  - Add role field to users table")
        print("  - Create product_audit_log table")
        print("  - Add creator tracking to products")
        print("  - Backfill existing data")
        print("\nA backup will be created automatically.")
        response = input("\nContinue with migration? (yes/no): ").lower()
        if response != 'yes':
            print("Migration cancelled.")
            sys.exit(0)

    success = run_migration(args.database)
    sys.exit(0 if success else 1)
