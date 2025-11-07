from database import get_db_connection
from datetime import datetime
import os

class Product:
    """Product model for inventory management"""

    def __init__(self, id, user_id, name, description, quantity, created_at, updated_at):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.description = description
        self.quantity = quantity
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create_product(user_id, name, description='', quantity=0, database_path='inventory.db'):
        """Create a new product"""
        conn = get_db_connection(database_path)
        try:
            cursor = conn.execute('''
                INSERT INTO products (user_id, name, description, quantity)
                VALUES (?, ?, ?, ?)
            ''', (user_id, name, description, quantity))

            product_id = cursor.lastrowid
            conn.commit()

            return Product.get_by_id(product_id, database_path)

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_by_id(product_id, database_path='inventory.db'):
        """Get product by ID"""
        conn = get_db_connection(database_path)
        try:
            product_data = conn.execute('''
                SELECT id, user_id, name, description, quantity, created_at, updated_at
                FROM products
                WHERE id = ?
            ''', (product_id,)).fetchone()

            if product_data:
                return Product(
                    id=product_data['id'],
                    user_id=product_data['user_id'],
                    name=product_data['name'],
                    description=product_data['description'],
                    quantity=product_data['quantity'],
                    created_at=product_data['created_at'],
                    updated_at=product_data['updated_at']
                )
            return None

        finally:
            conn.close()

    @staticmethod
    def get_by_user(user_id, limit=None, offset=0, search_term='', database_path='inventory.db'):
        """Get products by user ID with optional pagination and search"""
        conn = get_db_connection(database_path)
        try:
            query = '''
                SELECT id, user_id, name, description, quantity, created_at, updated_at
                FROM products
                WHERE user_id = ?
            '''
            params = [user_id]

            # Add search filter
            if search_term:
                query += ' AND (name LIKE ? OR description LIKE ?)'
                search_pattern = f'%{search_term}%'
                params.extend([search_pattern, search_pattern])

            # Add ordering
            query += ' ORDER BY updated_at DESC'

            # Add pagination
            if limit:
                query += ' LIMIT ? OFFSET ?'
                params.extend([limit, offset])

            products = []
            for row in conn.execute(query, params):
                products.append(Product(
                    id=row['id'],
                    user_id=row['user_id'],
                    name=row['name'],
                    description=row['description'],
                    quantity=row['quantity'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))

            return products

        finally:
            conn.close()

    def update(self, name=None, description=None, quantity=None, database_path='inventory.db'):
        """Update product details"""
        conn = get_db_connection(database_path)
        try:
            if name is not None:
                self.name = name
            if description is not None:
                self.description = description
            if quantity is not None:
                self.quantity = quantity

            conn.execute('''
                UPDATE products
                SET name = ?, description = ?, quantity = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (self.name, self.description, self.quantity, self.id))

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete(self, database_path='inventory.db'):
        """Delete product and associated data"""
        conn = get_db_connection(database_path)
        try:
            # Delete product (cascade will handle images and pricing)
            conn.execute('DELETE FROM products WHERE id = ?', (self.id,))
            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_pricing(self, database_path='inventory.db'):
        """Get pricing information for this product"""
        conn = get_db_connection(database_path)
        try:
            pricing_data = conn.execute('''
                SELECT buying_price, selling_price, mrp, updated_at
                FROM product_pricing
                WHERE product_id = ?
            ''', (self.id,)).fetchone()

            return dict(pricing_data) if pricing_data else None

        finally:
            conn.close()

    def set_pricing(self, buying_price=None, selling_price=None, mrp=None, database_path='inventory.db'):
        """Set or update pricing for this product"""
        conn = get_db_connection(database_path)
        try:
            # Check if pricing exists
            existing = conn.execute('''
                SELECT COUNT(*) as count FROM product_pricing WHERE product_id = ?
            ''', (self.id,)).fetchone()

            if existing['count'] > 0:
                # Update existing pricing
                conn.execute('''
                    UPDATE product_pricing
                    SET buying_price = ?, selling_price = ?, mrp = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = ?
                ''', (buying_price, selling_price, mrp, self.id))
            else:
                # Insert new pricing
                conn.execute('''
                    INSERT INTO product_pricing (product_id, buying_price, selling_price, mrp)
                    VALUES (?, ?, ?, ?)
                ''', (self.id, buying_price, selling_price, mrp))

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_images(self, database_path='inventory.db'):
        """Get all images for this product"""
        conn = get_db_connection(database_path)
        try:
            images = conn.execute('''
                SELECT id, filename, original_name, upload_date
                FROM product_images
                WHERE product_id = ?
                ORDER BY upload_date ASC
            ''', (self.id,)).fetchall()

            return [dict(img) for img in images]

        finally:
            conn.close()

    def add_image(self, filename, original_name, database_path='inventory.db'):
        """Add an image to this product"""
        conn = get_db_connection(database_path)
        try:
            cursor = conn.execute('''
                INSERT INTO product_images (product_id, filename, original_name)
                VALUES (?, ?, ?)
            ''', (self.id, filename, original_name))

            image_id = cursor.lastrowid
            conn.commit()
            return image_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def remove_image(self, image_id, upload_folder, database_path='inventory.db'):
        """Remove an image from this product"""
        conn = get_db_connection(database_path)
        try:
            # Get image info before deleting
            image_data = conn.execute('''
                SELECT filename FROM product_images
                WHERE id = ? AND product_id = ?
            ''', (image_id, self.id)).fetchone()

            if image_data:
                # Delete from database
                conn.execute('''
                    DELETE FROM product_images
                    WHERE id = ? AND product_id = ?
                ''', (image_id, self.id))

                # Delete physical file
                file_path = os.path.join(upload_folder, 'products', f'user_{self.user_id}', image_data['filename'])
                if os.path.exists(file_path):
                    os.remove(file_path)

                conn.commit()
                return True

            return False

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def to_dict(self, include_pricing=True, include_images=True, database_path='inventory.db'):
        """Convert product to dictionary"""
        product_dict = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'quantity': self.quantity,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        if include_pricing:
            product_dict['pricing'] = self.get_pricing(database_path)

        if include_images:
            product_dict['images'] = self.get_images(database_path)

        return product_dict

    @staticmethod
    def get_user_product_count(user_id, database_path='inventory.db'):
        """Get total number of products for a user"""
        conn = get_db_connection(database_path)
        try:
            result = conn.execute('''
                SELECT COUNT(*) as count
                FROM products
                WHERE user_id = ?
            ''', (user_id,)).fetchone()

            return result['count']

        finally:
            conn.close()

    def __repr__(self):
        return f'<Product {self.name}>'