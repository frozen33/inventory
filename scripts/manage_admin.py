#!/usr/bin/env python3
"""
Admin Management CLI Tool
Manage admin users for the inventory system
"""

import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db_connection


def list_all_users(database_path='inventory.db'):
    """List all users with their roles"""
    conn = get_db_connection(database_path)

    try:
        cursor = conn.execute('''
            SELECT u.id, u.email, u.role, u.created_at,
                   COUNT(DISTINCT p.id) as product_count,
                   COUNT(DISTINCT a.id) as activity_count
            FROM users u
            LEFT JOIN products p ON p.created_by = u.id
            LEFT JOIN product_audit_log a ON a.user_id = u.id
            GROUP BY u.id
            ORDER BY u.created_at
        ''')

        users = cursor.fetchall()

        if not users:
            print("No users found.")
            return

        print("\n" + "=" * 80)
        print("ALL USERS")
        print("=" * 80)
        print(f"{'ID':<5} {'Email':<30} {'Role':<10} {'Products':<10} {'Activity':<10} {'Created':<20}")
        print("-" * 80)

        for user in users:
            user_id, email, role, created_at, product_count, activity_count = user
            role_display = f"[{role.upper()}]" if role == 'admin' else role
            print(f"{user_id:<5} {email:<30} {role_display:<10} {product_count:<10} {activity_count:<10} {created_at:<20}")

        print("-" * 80)
        print(f"Total: {len(users)} users")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        conn.close()


def list_admins(database_path='inventory.db'):
    """List all admin users"""
    conn = get_db_connection(database_path)

    try:
        cursor = conn.execute('''
            SELECT id, email, created_at
            FROM users
            WHERE role = 'admin'
            ORDER BY created_at
        ''')

        admins = cursor.fetchall()

        if not admins:
            print("\n⚠️  No admin users found!")
            print("Create your first admin with: python scripts/manage_admin.py promote <email>\n")
            return

        print("\n" + "=" * 60)
        print("ADMIN USERS")
        print("=" * 60)
        print(f"{'ID':<5} {'Email':<35} {'Created':<20}")
        print("-" * 60)

        for admin in admins:
            admin_id, email, created_at = admin
            print(f"{admin_id:<5} {email:<35} {created_at:<20}")

        print("-" * 60)
        print(f"Total: {len(admins)} admin(s)")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"Error listing admins: {e}")
    finally:
        conn.close()


def promote_user(email, database_path='inventory.db'):
    """Promote a user to admin"""
    conn = get_db_connection(database_path)

    try:
        # Check if user exists
        cursor = conn.execute('SELECT id, email, role FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if not user:
            print(f"✗ User not found: {email}")
            return False

        user_id, user_email, current_role = user

        if current_role == 'admin':
            print(f"ℹ️  User {user_email} is already an admin.")
            return True

        # Promote to admin
        conn.execute('UPDATE users SET role = ? WHERE id = ?', ('admin', user_id))
        conn.commit()

        print(f"✓ User {user_email} (ID: {user_id}) promoted to admin!")
        return True

    except Exception as e:
        print(f"✗ Error promoting user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def demote_user(email, database_path='inventory.db'):
    """Demote an admin to regular user"""
    conn = get_db_connection(database_path)

    try:
        # Check if user exists
        cursor = conn.execute('SELECT id, email, role FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if not user:
            print(f"✗ User not found: {email}")
            return False

        user_id, user_email, current_role = user

        if current_role != 'admin':
            print(f"ℹ️  User {user_email} is not an admin.")
            return True

        # Check if this is the last admin
        cursor = conn.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('admin',))
        admin_count = cursor.fetchone()[0]

        if admin_count <= 1:
            print(f"✗ Cannot demote the last admin user!")
            print("   Promote another user to admin first.")
            return False

        # Demote to regular user
        conn.execute('UPDATE users SET role = ? WHERE id = ?', ('user', user_id))
        conn.commit()

        print(f"✓ User {user_email} (ID: {user_id}) demoted to regular user.")
        return True

    except Exception as e:
        print(f"✗ Error demoting user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def show_user_info(email, database_path='inventory.db'):
    """Show detailed information about a user"""
    conn = get_db_connection(database_path)

    try:
        # Get user info
        cursor = conn.execute('''
            SELECT u.id, u.email, u.role, u.created_at,
                   COUNT(DISTINCT p.id) as product_count
            FROM users u
            LEFT JOIN products p ON p.created_by = u.id
            WHERE u.email = ?
            GROUP BY u.id
        ''', (email,))

        user = cursor.fetchone()

        if not user:
            print(f"✗ User not found: {email}")
            return False

        user_id, user_email, role, created_at, product_count = user

        print("\n" + "=" * 60)
        print("USER INFORMATION")
        print("=" * 60)
        print(f"ID:              {user_id}")
        print(f"Email:           {user_email}")
        print(f"Role:            {role.upper() if role == 'admin' else role}")
        print(f"Created:         {created_at}")
        print(f"Products:        {product_count} created")

        # Get recent activity
        cursor = conn.execute('''
            SELECT action, COUNT(*) as count
            FROM product_audit_log
            WHERE user_id = ?
            GROUP BY action
        ''', (user_id,))

        activities = cursor.fetchall()

        if activities:
            print("\nActivity:")
            for action, count in activities:
                print(f"  - {action}: {count}")

        print("=" * 60 + "\n")
        return True

    except Exception as e:
        print(f"Error getting user info: {e}")
        return False
    finally:
        conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Manage admin users for the inventory system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # List all users
  python scripts/manage_admin.py list-users

  # List only admins
  python scripts/manage_admin.py list-admins

  # Promote user to admin
  python scripts/manage_admin.py promote user@example.com

  # Demote admin to regular user
  python scripts/manage_admin.py demote admin@example.com

  # Show user information
  python scripts/manage_admin.py info user@example.com
        '''
    )

    parser.add_argument('command', choices=['promote', 'demote', 'list-users', 'list-admins', 'info'],
                       help='Command to execute')
    parser.add_argument('email', nargs='?', help='User email address (required for promote/demote/info)')
    parser.add_argument('--database', default='inventory.db', help='Path to database file')

    args = parser.parse_args()

    # Check if database exists
    if not os.path.exists(args.database):
        print(f"✗ Database not found: {args.database}")
        print("Make sure you're running this from the inventory-app directory.")
        sys.exit(1)

    # Check if migration has been run
    try:
        conn = get_db_connection(args.database)
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        if 'role' not in columns:
            print("✗ Migration not applied!")
            print("Run the migration first: python migrations/add_collaborative_features.py")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Error checking database: {e}")
        sys.exit(1)

    # Execute command
    if args.command == 'list-users':
        list_all_users(args.database)

    elif args.command == 'list-admins':
        list_admins(args.database)

    elif args.command == 'promote':
        if not args.email:
            print("✗ Email required for promote command")
            print("Usage: python scripts/manage_admin.py promote <email>")
            sys.exit(1)
        success = promote_user(args.email, args.database)
        sys.exit(0 if success else 1)

    elif args.command == 'demote':
        if not args.email:
            print("✗ Email required for demote command")
            print("Usage: python scripts/manage_admin.py demote <email>")
            sys.exit(1)
        success = demote_user(args.email, args.database)
        sys.exit(0 if success else 1)

    elif args.command == 'info':
        if not args.email:
            print("✗ Email required for info command")
            print("Usage: python scripts/manage_admin.py info <email>")
            sys.exit(1)
        success = show_user_info(args.email, args.database)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
