"""
Tile Details Model
Stores tile-specific information for products
"""

from database import get_db_connection


class TileDetails:
    """Model for tile-specific product details"""

    def __init__(self, id, product_id, tiles_per_box, number_of_boxes,
                 dimension_length, dimension_width, dimension_unit, sq_feet_per_box,
                 created_at, updated_at):
        self.id = id
        self.product_id = product_id
        self.tiles_per_box = tiles_per_box
        self.number_of_boxes = number_of_boxes
        self.dimension_length = dimension_length
        self.dimension_width = dimension_width
        self.dimension_unit = dimension_unit
        self.sq_feet_per_box = sq_feet_per_box
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(product_id, tiles_per_box=None, number_of_boxes=None,
               dimension_length=None, dimension_width=None, dimension_unit='feet',
               sq_feet_per_box=None, database_path='inventory.db'):
        """Create tile details for a product"""
        conn = get_db_connection(database_path)
        try:
            cursor = conn.execute('''
                INSERT INTO tiles_details
                (product_id, tiles_per_box, number_of_boxes, dimension_length,
                 dimension_width, dimension_unit, sq_feet_per_box)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (product_id, tiles_per_box, number_of_boxes, dimension_length,
                  dimension_width, dimension_unit, sq_feet_per_box))

            tile_id = cursor.lastrowid
            conn.commit()

            return TileDetails.get_by_product_id(product_id, database_path)

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_by_product_id(product_id, database_path='inventory.db'):
        """Get tile details by product ID"""
        conn = get_db_connection(database_path)
        try:
            tile_data = conn.execute('''
                SELECT id, product_id, tiles_per_box, number_of_boxes,
                       dimension_length, dimension_width, dimension_unit,
                       sq_feet_per_box, created_at, updated_at
                FROM tiles_details
                WHERE product_id = ?
            ''', (product_id,)).fetchone()

            if tile_data:
                return TileDetails(
                    id=tile_data['id'],
                    product_id=tile_data['product_id'],
                    tiles_per_box=tile_data['tiles_per_box'],
                    number_of_boxes=tile_data['number_of_boxes'],
                    dimension_length=tile_data['dimension_length'],
                    dimension_width=tile_data['dimension_width'],
                    dimension_unit=tile_data['dimension_unit'],
                    sq_feet_per_box=tile_data['sq_feet_per_box'],
                    created_at=tile_data['created_at'],
                    updated_at=tile_data['updated_at']
                )
            return None

        finally:
            conn.close()

    def update(self, tiles_per_box=None, number_of_boxes=None,
               dimension_length=None, dimension_width=None, dimension_unit=None,
               sq_feet_per_box=None, database_path='inventory.db'):
        """Update tile details"""
        conn = get_db_connection(database_path)
        try:
            if tiles_per_box is not None:
                self.tiles_per_box = tiles_per_box
            if number_of_boxes is not None:
                self.number_of_boxes = number_of_boxes
            if dimension_length is not None:
                self.dimension_length = dimension_length
            if dimension_width is not None:
                self.dimension_width = dimension_width
            if dimension_unit is not None:
                self.dimension_unit = dimension_unit
            if sq_feet_per_box is not None:
                self.sq_feet_per_box = sq_feet_per_box

            conn.execute('''
                UPDATE tiles_details
                SET tiles_per_box = ?, number_of_boxes = ?,
                    dimension_length = ?, dimension_width = ?, dimension_unit = ?,
                    sq_feet_per_box = ?, updated_at = CURRENT_TIMESTAMP
                WHERE product_id = ?
            ''', (self.tiles_per_box, self.number_of_boxes,
                  self.dimension_length, self.dimension_width, self.dimension_unit,
                  self.sq_feet_per_box, self.product_id))

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def to_dict(self):
        """Convert tile details to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'tiles_per_box': self.tiles_per_box,
            'number_of_boxes': self.number_of_boxes,
            'dimension_length': self.dimension_length,
            'dimension_width': self.dimension_width,
            'dimension_unit': self.dimension_unit,
            'dimension_display': f"{self.dimension_length} x {self.dimension_width} {self.dimension_unit}" if self.dimension_length and self.dimension_width else None,
            'sq_feet_per_box': self.sq_feet_per_box,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def __repr__(self):
        return f'<TileDetails for Product {self.product_id}>'
