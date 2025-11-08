from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection
from datetime import datetime

class User(UserMixin):
    """User model for authentication"""

    def __init__(self, id, email, password_hash, created_at, role='user'):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
        self.role = role

    @staticmethod
    def create_user(email, password, database_path='inventory.db'):
        """Create a new user"""
        password_hash = generate_password_hash(password)

        conn = get_db_connection(database_path)
        try:
            cursor = conn.execute('''
                INSERT INTO users (email, password_hash)
                VALUES (?, ?)
            ''', (email, password_hash))

            user_id = cursor.lastrowid
            conn.commit()

            return User.get_by_id(user_id, database_path)

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_by_id(user_id, database_path='inventory.db'):
        """Get user by ID"""
        conn = get_db_connection(database_path)
        try:
            user_data = conn.execute('''
                SELECT id, email, password_hash, created_at, role
                FROM users
                WHERE id = ?
            ''', (user_id,)).fetchone()

            if user_data:
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    created_at=user_data['created_at'],
                    role=user_data['role'] or 'user'
                )
            return None

        finally:
            conn.close()

    @staticmethod
    def get_by_email(email, database_path='inventory.db'):
        """Get user by email"""
        conn = get_db_connection(database_path)
        try:
            user_data = conn.execute('''
                SELECT id, email, password_hash, created_at, role
                FROM users
                WHERE email = ?
            ''', (email,)).fetchone()

            if user_data:
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    created_at=user_data['created_at'],
                    role=user_data['role'] or 'user'
                )
            return None

        finally:
            conn.close()

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    def update_password(self, new_password, database_path='inventory.db'):
        """Update user password"""
        new_hash = generate_password_hash(new_password)

        conn = get_db_connection(database_path)
        try:
            conn.execute('''
                UPDATE users
                SET password_hash = ?
                WHERE id = ?
            ''', (new_hash, self.id))

            conn.commit()
            self.password_hash = new_hash
            return True

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def email_exists(email, database_path='inventory.db'):
        """Check if email already exists"""
        conn = get_db_connection(database_path)
        try:
            result = conn.execute('''
                SELECT COUNT(*) as count
                FROM users
                WHERE email = ?
            ''', (email,)).fetchone()

            return result['count'] > 0

        finally:
            conn.close()

    def get_product_count(self, database_path='inventory.db'):
        """Get number of products for this user"""
        conn = get_db_connection(database_path)
        try:
            result = conn.execute('''
                SELECT COUNT(*) as count
                FROM products
                WHERE user_id = ?
            ''', (self.id,)).fetchone()

            return result['count']

        finally:
            conn.close()

    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'

    @staticmethod
    def get_all_users(database_path='inventory.db'):
        """Get all users with their stats (admin only)"""
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

            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'email': row[1],
                    'role': row[2],
                    'created_at': row[3],
                    'product_count': row[4],
                    'activity_count': row[5]
                })

            return users

        finally:
            conn.close()

    @staticmethod
    def promote_to_admin(user_id, database_path='inventory.db'):
        """Promote user to admin role"""
        conn = get_db_connection(database_path)
        try:
            conn.execute('UPDATE users SET role = ? WHERE id = ?', ('admin', user_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error promoting user: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def demote_from_admin(user_id, database_path='inventory.db'):
        """Demote admin to regular user role"""
        conn = get_db_connection(database_path)
        try:
            # Check if this is the last admin
            cursor = conn.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('admin',))
            admin_count = cursor.fetchone()[0]

            if admin_count <= 1:
                return False  # Can't demote the last admin

            conn.execute('UPDATE users SET role = ? WHERE id = ?', ('user', user_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error demoting user: {e}")
            return False
        finally:
            conn.close()

    def to_dict(self):
        """Convert user to dictionary (excluding password)"""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'is_admin': self.is_admin(),
            'created_at': self.created_at,
            'product_count': self.get_product_count()
        }

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'