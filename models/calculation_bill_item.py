"""
CalculationBillItem model for individual items in calculation bills
"""

from database import get_db_connection


class CalculationBillItem:
    """Model for calculation bill items"""

    def __init__(self, id=None, bill_id=None, product_id=None, source_type=None,
                 calculation_type=None, tile_name=None, dimensions=None,
                 tiles_per_box=None, coverage_per_box=None, room_dimensions=None,
                 area_calculated=None, boxes_exact=None, boxes_needed=None,
                 price_per_box=None, total_price=None, created_at=None):
        self.id = id
        self.bill_id = bill_id
        self.product_id = product_id
        self.source_type = source_type
        self.calculation_type = calculation_type
        self.tile_name = tile_name
        self.dimensions = dimensions
        self.tiles_per_box = tiles_per_box
        self.coverage_per_box = coverage_per_box
        self.room_dimensions = room_dimensions
        self.area_calculated = area_calculated
        self.boxes_exact = boxes_exact
        self.boxes_needed = boxes_needed
        self.price_per_box = price_per_box
        self.total_price = total_price
        self.created_at = created_at

    @staticmethod
    def create(bill_id, calculation_data):
        """
        Create a new bill item

        Args:
            bill_id: ID of the parent bill
            calculation_data: Dictionary containing calculation results and metadata

        Returns:
            Item ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO calculation_bill_items (
                bill_id, product_id, source_type, calculation_type,
                tile_name, dimensions, tiles_per_box, coverage_per_box,
                room_dimensions, area_calculated, boxes_exact, boxes_needed,
                price_per_box, total_price
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bill_id,
            calculation_data.get('product_id'),
            calculation_data.get('source_type'),
            calculation_data.get('calculation_type'),
            calculation_data.get('tile_name'),
            calculation_data.get('dimensions'),
            calculation_data.get('tiles_per_box'),
            calculation_data.get('coverage_per_box'),
            calculation_data.get('room_dimensions'),
            calculation_data.get('area_calculated'),
            calculation_data.get('boxes_exact'),
            calculation_data.get('boxes_needed'),
            calculation_data.get('price_per_box'),
            calculation_data.get('total_price')
        ))

        item_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return item_id

    @staticmethod
    def get_by_bill_id(bill_id):
        """Get all items for a specific bill"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, bill_id, product_id, source_type, calculation_type,
                   tile_name, dimensions, tiles_per_box, coverage_per_box,
                   room_dimensions, area_calculated, boxes_exact, boxes_needed,
                   price_per_box, total_price, created_at
            FROM calculation_bill_items
            WHERE bill_id = ?
            ORDER BY created_at
        """, (bill_id,))

        rows = cursor.fetchall()
        conn.close()

        items = []
        for row in rows:
            items.append(CalculationBillItem(
                id=row[0],
                bill_id=row[1],
                product_id=row[2],
                source_type=row[3],
                calculation_type=row[4],
                tile_name=row[5],
                dimensions=row[6],
                tiles_per_box=row[7],
                coverage_per_box=row[8],
                room_dimensions=row[9],
                area_calculated=row[10],
                boxes_exact=row[11],
                boxes_needed=row[12],
                price_per_box=row[13],
                total_price=row[14],
                created_at=row[15]
            ))

        return items

    @staticmethod
    def delete(item_id):
        """Delete a bill item"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM calculation_bill_items WHERE id = ?", (item_id,))

        conn.commit()
        conn.close()

    @staticmethod
    def delete_by_bill_id(bill_id):
        """Delete all items for a bill"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM calculation_bill_items WHERE bill_id = ?", (bill_id,))

        conn.commit()
        conn.close()

    def to_dict(self):
        """Convert item to dictionary"""
        return {
            'id': self.id,
            'bill_id': self.bill_id,
            'product_id': self.product_id,
            'source_type': self.source_type,
            'calculation_type': self.calculation_type,
            'tile_name': self.tile_name,
            'dimensions': self.dimensions,
            'tiles_per_box': self.tiles_per_box,
            'coverage_per_box': float(self.coverage_per_box) if self.coverage_per_box else 0.0,
            'room_dimensions': self.room_dimensions,
            'area_calculated': float(self.area_calculated) if self.area_calculated else 0.0,
            'boxes_exact': float(self.boxes_exact) if self.boxes_exact else 0.0,
            'boxes_needed': self.boxes_needed,
            'price_per_box': float(self.price_per_box) if self.price_per_box else None,
            'total_price': float(self.total_price) if self.total_price else None,
            'created_at': self.created_at
        }
