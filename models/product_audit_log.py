"""
Product Audit Log Model
Tracks all changes to products for accountability in collaborative inventory
"""

import json
from datetime import datetime
from database import get_db_connection


class ProductAuditLog:
    """Model for tracking product changes"""

    def __init__(self, id, product_id, user_id, action, product_name, changes, timestamp):
        self.id = id
        self.product_id = product_id
        self.user_id = user_id
        self.action = action
        self.product_name = product_name
        self.changes = changes
        self.timestamp = timestamp

    @staticmethod
    def log_create(product_id, user_id, product_name, database_path='inventory.db'):
        """Log product creation"""
        conn = get_db_connection(database_path)
        try:
            conn.execute('''
                INSERT INTO product_audit_log (product_id, user_id, action, product_name)
                VALUES (?, ?, ?, ?)
            ''', (product_id, user_id, 'create', product_name))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error logging product creation: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def log_update(product_id, user_id, product_name, changes_dict, database_path='inventory.db'):
        """
        Log product update with changes dictionary

        changes_dict example: {
            'name': {'old': 'Old Name', 'new': 'New Name'},
            'price': {'old': 100.0, 'new': 150.0}
        }
        """
        conn = get_db_connection(database_path)
        try:
            # Convert changes to JSON string
            changes_json = json.dumps(changes_dict) if changes_dict else None

            conn.execute('''
                INSERT INTO product_audit_log (product_id, user_id, action, product_name, changes)
                VALUES (?, ?, ?, ?, ?)
            ''', (product_id, user_id, 'update', product_name, changes_json))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error logging product update: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def log_delete(product_id, user_id, product_name, database_path='inventory.db'):
        """Log product deletion"""
        conn = get_db_connection(database_path)
        try:
            conn.execute('''
                INSERT INTO product_audit_log (product_id, user_id, action, product_name)
                VALUES (?, ?, ?, ?)
            ''', (product_id, user_id, 'delete', product_name))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error logging product deletion: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def log_image_add(product_id, user_id, product_name, image_filename, database_path='inventory.db'):
        """Log image addition to product"""
        conn = get_db_connection(database_path)
        try:
            changes = {'image_added': image_filename}
            changes_json = json.dumps(changes)

            conn.execute('''
                INSERT INTO product_audit_log (product_id, user_id, action, product_name, changes)
                VALUES (?, ?, ?, ?, ?)
            ''', (product_id, user_id, 'update', product_name, changes_json))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error logging image addition: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def log_image_delete(product_id, user_id, product_name, image_filename, database_path='inventory.db'):
        """Log image deletion from product"""
        conn = get_db_connection(database_path)
        try:
            changes = {'image_deleted': image_filename}
            changes_json = json.dumps(changes)

            conn.execute('''
                INSERT INTO product_audit_log (product_id, user_id, action, product_name, changes)
                VALUES (?, ?, ?, ?, ?)
            ''', (product_id, user_id, 'update', product_name, changes_json))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error logging image deletion: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def get_product_history(product_id, limit=50, database_path='inventory.db'):
        """Get all audit logs for a specific product"""
        conn = get_db_connection(database_path)
        try:
            cursor = conn.execute('''
                SELECT a.id, a.product_id, a.user_id, a.action, a.product_name,
                       a.changes, a.timestamp, u.email
                FROM product_audit_log a
                LEFT JOIN users u ON u.id = a.user_id
                WHERE a.product_id = ?
                ORDER BY a.timestamp DESC
                LIMIT ?
            ''', (product_id, limit))

            logs = []
            for row in cursor.fetchall():
                log = {
                    'id': row[0],
                    'product_id': row[1],
                    'user_id': row[2],
                    'action': row[3],
                    'product_name': row[4],
                    'changes': json.loads(row[5]) if row[5] else None,
                    'timestamp': row[6],
                    'user_email': row[7]
                }
                logs.append(log)

            return logs
        except Exception as e:
            print(f"Error getting product history: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_user_activity(user_id, limit=50, database_path='inventory.db'):
        """Get recent activity by a specific user"""
        conn = get_db_connection(database_path)
        try:
            cursor = conn.execute('''
                SELECT a.id, a.product_id, a.user_id, a.action, a.product_name,
                       a.changes, a.timestamp, u.email
                FROM product_audit_log a
                LEFT JOIN users u ON u.id = a.user_id
                WHERE a.user_id = ?
                ORDER BY a.timestamp DESC
                LIMIT ?
            ''', (user_id, limit))

            logs = []
            for row in cursor.fetchall():
                log = {
                    'id': row[0],
                    'product_id': row[1],
                    'user_id': row[2],
                    'action': row[3],
                    'product_name': row[4],
                    'changes': json.loads(row[5]) if row[5] else None,
                    'timestamp': row[6],
                    'user_email': row[7]
                }
                logs.append(log)

            return logs
        except Exception as e:
            print(f"Error getting user activity: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_recent_activity(limit=100, database_path='inventory.db'):
        """Get recent activity across all products (admin only)"""
        conn = get_db_connection(database_path)
        try:
            cursor = conn.execute('''
                SELECT a.id, a.product_id, a.user_id, a.action, a.product_name,
                       a.changes, a.timestamp, u.email
                FROM product_audit_log a
                LEFT JOIN users u ON u.id = a.user_id
                ORDER BY a.timestamp DESC
                LIMIT ?
            ''', (limit,))

            logs = []
            for row in cursor.fetchall():
                log = {
                    'id': row[0],
                    'product_id': row[1],
                    'user_id': row[2],
                    'action': row[3],
                    'product_name': row[4],
                    'changes': json.loads(row[5]) if row[5] else None,
                    'timestamp': row[6],
                    'user_email': row[7]
                }
                logs.append(log)

            return logs
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_activity_stats(database_path='inventory.db'):
        """Get activity statistics for admin dashboard"""
        conn = get_db_connection(database_path)
        try:
            # Total actions
            cursor = conn.execute('SELECT COUNT(*) FROM product_audit_log')
            total_actions = cursor.fetchone()[0]

            # Actions by type
            cursor = conn.execute('''
                SELECT action, COUNT(*) as count
                FROM product_audit_log
                GROUP BY action
            ''')
            actions_by_type = {row[0]: row[1] for row in cursor.fetchall()}

            # Most active users
            cursor = conn.execute('''
                SELECT u.email, COUNT(a.id) as action_count
                FROM product_audit_log a
                LEFT JOIN users u ON u.id = a.user_id
                GROUP BY a.user_id
                ORDER BY action_count DESC
                LIMIT 5
            ''')
            most_active_users = [{'email': row[0], 'count': row[1]} for row in cursor.fetchall()]

            # Recent activity (last 24 hours)
            cursor = conn.execute('''
                SELECT COUNT(*)
                FROM product_audit_log
                WHERE datetime(timestamp) >= datetime('now', '-1 day')
            ''')
            actions_last_24h = cursor.fetchone()[0]

            return {
                'total_actions': total_actions,
                'actions_by_type': actions_by_type,
                'most_active_users': most_active_users,
                'actions_last_24h': actions_last_24h
            }
        except Exception as e:
            print(f"Error getting activity stats: {e}")
            return {
                'total_actions': 0,
                'actions_by_type': {},
                'most_active_users': [],
                'actions_last_24h': 0
            }
        finally:
            conn.close()

    def __repr__(self):
        return f"<AuditLog {self.action} on product {self.product_id} by user {self.user_id}>"
