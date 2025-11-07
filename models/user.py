from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection
from datetime import datetime

class User(UserMixin):
    """User model for authentication"""

    def __init__(self, id, email, password_hash, created_at):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at

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
                SELECT id, email, password_hash, created_at
                FROM users
                WHERE id = ?
            ''', (user_id,)).fetchone()

            if user_data:
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    created_at=user_data['created_at']
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
                SELECT id, email, password_hash, created_at
                FROM users
                WHERE email = ?
            ''', (email,)).fetchone()

            if user_data:
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    created_at=user_data['created_at']
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

    def to_dict(self):
        """Convert user to dictionary (excluding password)"""
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at,
            'product_count': self.get_product_count()
        }

    def __repr__(self):
        return f'<User {self.email}>'