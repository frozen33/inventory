import sqlite3
import os
from datetime import datetime

def get_db_connection(database_path='inventory.db'):
    """Get database connection with proper configuration"""
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name

    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys = ON')

    # Set WAL mode for better concurrency
    conn.execute('PRAGMA journal_mode = WAL')

    return conn

def init_db(database_path='inventory.db'):
    """Initialize the database with all required tables"""

    # Remove existing database for fresh start
    if os.path.exists(database_path):
        os.remove(database_path)
        print(f"Removed existing database: {database_path}")

    conn = get_db_connection(database_path)

    try:
        # Create users table
        conn.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create products table
        conn.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                quantity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')

        # Create product_images table
        conn.execute('''
            CREATE TABLE product_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        ''')

        # Create product_pricing table
        conn.execute('''
            CREATE TABLE product_pricing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER UNIQUE NOT NULL,
                buying_price DECIMAL(10,2),
                selling_price DECIMAL(10,2),
                mrp DECIMAL(10,2),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        ''')

        # Create indexes for better performance
        conn.execute('CREATE INDEX idx_products_user_id ON products(user_id)')
        conn.execute('CREATE INDEX idx_product_images_product_id ON product_images(product_id)')
        conn.execute('CREATE INDEX idx_product_pricing_product_id ON product_pricing(product_id)')
        conn.execute('CREATE INDEX idx_users_email ON users(email)')

        conn.commit()
        print("Database initialized successfully!")
        print("Created tables: users, products, product_images, product_pricing")

    except Exception as e:
        conn.rollback()
        print(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()

def create_test_data(database_path='inventory.db'):
    """Create some test data for development"""
    from werkzeug.security import generate_password_hash

    conn = get_db_connection(database_path)

    try:
        # Create test user
        password_hash = generate_password_hash('testpass123')
        cursor = conn.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', ('test@example.com', password_hash))

        user_id = cursor.lastrowid

        # Create test products
        test_products = [
            ('Smartphone', 'Latest model smartphone with great features'),
            ('Laptop', 'High-performance laptop for work and gaming'),
            ('Headphones', 'Wireless noise-canceling headphones')
        ]

        for name, description in test_products:
            # Insert product
            cursor = conn.execute('''
                INSERT INTO products (user_id, name, description, quantity)
                VALUES (?, ?, ?, ?)
            ''', (user_id, name, description, 25))

            product_id = cursor.lastrowid

            # Insert pricing
            conn.execute('''
                INSERT INTO product_pricing (product_id, buying_price, selling_price, mrp)
                VALUES (?, ?, ?, ?)
            ''', (product_id, 100.00, 150.00, 200.00))

        conn.commit()
        print("Test data created successfully!")
        print("Test user: test@example.com / testpass123")

    except Exception as e:
        conn.rollback()
        print(f"Error creating test data: {e}")
        raise
    finally:
        conn.close()

def check_database(database_path='inventory.db'):
    """Check database structure and data"""
    if not os.path.exists(database_path):
        print(f"Database {database_path} does not exist!")
        return

    conn = get_db_connection(database_path)

    try:
        # Check tables
        tables = conn.execute('''
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ''').fetchall()

        print(f"Database: {database_path}")
        print(f"Tables: {[table[0] for table in tables]}")

        # Check data counts
        for table in tables:
            table_name = table[0]
            count = conn.execute(f'SELECT COUNT(*) FROM {table_name}').fetchone()[0]
            print(f"{table_name}: {count} records")

    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    # Initialize database when run directly
    database_path = 'inventory.db'

    print("Initializing database...")
    init_db(database_path)

    print("\nCreating test data...")
    create_test_data(database_path)

    print("\nDatabase status:")
    check_database(database_path)