"""
CalculationBill model for managing saved calculation bills
"""

from database import get_db_connection
from datetime import datetime, timedelta


class CalculationBill:
    """Model for calculation bills"""

    def __init__(self, id=None, user_id=None, bill_name=None, total_boxes=0,
                 total_price=0.0, created_at=None, created_by=None):
        self.id = id
        self.user_id = user_id
        self.bill_name = bill_name
        self.total_boxes = total_boxes
        self.total_price = total_price
        self.created_at = created_at
        self.created_by = created_by

    @staticmethod
    def create(user_id, created_by, bill_name=None):
        """
        Create a new calculation bill

        Args:
            user_id: ID of the user creating the bill
            created_by: Email/name of the user
            bill_name: Optional name for the bill

        Returns:
            Bill ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO calculation_bills (user_id, bill_name, created_by, total_boxes, total_price)
            VALUES (?, ?, ?, 0, 0)
        """, (user_id, bill_name, created_by))

        bill_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return bill_id

    @staticmethod
    def get_by_id(bill_id):
        """Get a bill by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, user_id, bill_name, total_boxes, total_price, created_at, created_by
            FROM calculation_bills
            WHERE id = ?
        """, (bill_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return CalculationBill(
                id=row[0],
                user_id=row[1],
                bill_name=row[2],
                total_boxes=row[3],
                total_price=row[4],
                created_at=row[5],
                created_by=row[6]
            )
        return None

    @staticmethod
    def get_all(order_by='created_at DESC', limit=None):
        """
        Get all bills (shared view)

        Args:
            order_by: SQL ORDER BY clause
            limit: Maximum number of results

        Returns:
            List of CalculationBill objects
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        query = f"""
            SELECT id, user_id, bill_name, total_boxes, total_price, created_at, created_by
            FROM calculation_bills
            ORDER BY {order_by}
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        bills = []
        for row in rows:
            bills.append(CalculationBill(
                id=row[0],
                user_id=row[1],
                bill_name=row[2],
                total_boxes=row[3],
                total_price=row[4],
                created_at=row[5],
                created_by=row[6]
            ))

        return bills

    @staticmethod
    def get_all_by_user(user_id, order_by='created_at DESC'):
        """Get all bills for a specific user"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT id, user_id, bill_name, total_boxes, total_price, created_at, created_by
            FROM calculation_bills
            WHERE user_id = ?
            ORDER BY {order_by}
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        bills = []
        for row in rows:
            bills.append(CalculationBill(
                id=row[0],
                user_id=row[1],
                bill_name=row[2],
                total_boxes=row[3],
                total_price=row[4],
                created_at=row[5],
                created_by=row[6]
            ))

        return bills

    @staticmethod
    def update_totals(bill_id, total_boxes, total_price):
        """Update the total boxes and price for a bill"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE calculation_bills
            SET total_boxes = ?, total_price = ?
            WHERE id = ?
        """, (total_boxes, total_price, bill_id))

        conn.commit()
        conn.close()

    @staticmethod
    def delete(bill_id):
        """Delete a bill (cascade deletes items)"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM calculation_bills WHERE id = ?", (bill_id,))

        conn.commit()
        conn.close()

    @staticmethod
    def delete_older_than_days(days=30):
        """
        Delete bills older than specified days

        Args:
            days: Number of days (default 30)

        Returns:
            Number of bills deleted
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)

        cursor.execute("""
            DELETE FROM calculation_bills
            WHERE created_at < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    @staticmethod
    def get_count_older_than_days(days=30):
        """Get count of bills older than specified days"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)

        cursor.execute("""
            SELECT COUNT(*) FROM calculation_bills
            WHERE created_at < ?
        """, (cutoff_date,))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    def to_dict(self):
        """Convert bill to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'bill_name': self.bill_name,
            'total_boxes': self.total_boxes,
            'total_price': float(self.total_price) if self.total_price else 0.0,
            'created_at': self.created_at,
            'created_by': self.created_by
        }
