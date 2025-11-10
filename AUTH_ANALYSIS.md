# Inventory App - Authentication & Authorization Analysis

## 1. Current User Model Structure

### User Model Fields (from models/user.py)
The User class uses Flask-Login's UserMixin for session management.

**Database Fields (users table):**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT): Unique user identifier
- `email` (TEXT UNIQUE NOT NULL): User's email address
- `password_hash` (TEXT NOT NULL): Bcrypt hashed password via werkzeug
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP): Account creation timestamp

**User Object Properties:**
- `id`: User ID from database
- `email`: User email address
- `password_hash`: Hashed password
- `created_at`: Creation timestamp
- `is_authenticated`: Inherited from UserMixin (True if logged in)
- `is_active`: Inherited from UserMixin (always True)
- `is_anonymous`: Inherited from UserMixin (False for users)

### User Model Methods

**Static Methods (Class-level):**
1. `create_user(email, password, database_path)`: Creates new user account
   - Hashes password using werkzeug.security.generate_password_hash
   - Inserts into database
   - Returns User object

2. `get_by_id(user_id, database_path)`: Retrieves user by ID
   - Used by Flask-Login user_loader callback
   - Returns User object or None

3. `get_by_email(email, database_path)`: Retrieves user by email
   - Used during login for credential lookup
   - Returns User object or None

4. `email_exists(email, database_path)`: Checks if email already registered
   - Used during registration validation
   - Returns boolean

5. `get_user_product_count(user_id, database_path)`: Gets total products
   - Counts products for user
   - Returns integer count

**Instance Methods:**
1. `check_password(password)`: Validates password
   - Compares plaintext against password_hash
   - Returns boolean

2. `update_password(new_password, database_path)`: Changes password
   - Hashes new password
   - Updates database
   - Returns True on success

3. `get_product_count(database_path)`: Gets product count
   - Wrapper method for counting user's products
   - Returns integer

4. `to_dict()`: Serializes user to dictionary
   - Returns id, email, created_at, product_count
   - Excludes password_hash

5. `__repr__()`: String representation
   - Returns '<User email@domain.com>'

---

## 2. Authentication Flow

### Registration Flow (routes/auth.py - lines 66-115)

```
GET /auth/register
  └─> Display registration form

POST /auth/register
  ├─> Validate inputs
  │   ├─ Check email format (regex validation)
  │   ├─ Check password strength (min 6, max 128 chars)
  │   ├─ Check passwords match
  │   └─ Check email not already registered
  ├─> Create user via User.create_user()
  │   └─> Hash password with generate_password_hash()
  ├─> Auto-login user via login_user()
  └─> Redirect to /inventory/dashboard
```

**Validation Rules:**
- Email: Valid format via regex `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Password: 6-128 characters
- Confirmed: Password confirmation must match

### Login Flow (routes/auth.py - lines 24-64)

```
GET /auth/login
  └─> Display login form

POST /auth/login
  ├─> Validate inputs
  │   ├─ Check email & password provided
  │   └─ Validate email format
  ├─> Lookup user via User.get_by_email()
  ├─> Check password via user.check_password()
  ├─> If valid:
  │   ├─> login_user(user, remember=remember)
  │   └─> Redirect to next page or dashboard
  └─> If invalid:
      └─> Show error message
```

**Key Features:**
- "Remember me" checkbox support (7-day session)
- Email case-insensitive (lowercased on input)
- Generic error message (doesn't reveal if email exists)
- Redirect to next page after login (security-aware)

### Session Management (app.py - lines 15-26)

```python
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id), app.config['DATABASE_PATH'])
```

**Session Configuration (config.py):**
- Session lifetime: 7 days
- Remember cookie duration: 7 days
- HttpOnly flag: True (prevents JavaScript access)
- SameSite: Lax (CSRF protection)

### Logout Flow (routes/auth.py - lines 117-124)

```
POST /auth/logout
  ├─> @login_required decorator checks session
  ├─> logout_user() clears session
  └─> Redirect to /auth/login
```

### Other Auth Routes

**Profile Page** (routes/auth.py - lines 126-130)
- Protected with @login_required
- Displays current_user info
- No modifications available

**Change Password** (routes/auth.py - lines 132-172)
- Protected with @login_required
- Validates current password first
- Password strength validation
- Cannot reuse current password

---

## 3. Current Database Schema for Users

### Users Table Structure

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Schema Details:**
- `id`: Autoincrementing primary key
- `email`: Unique constraint prevents duplicate accounts
- `password_hash`: Werkzeug bcrypt hash (uses BCRYPT)
- `created_at`: Auto-set to current timestamp on insert

**Indexes:**
- `idx_users_email`: Index on email column for login lookups
  - Improves query performance for get_by_email()

**Foreign Key Relationships:**
- `products.user_id` → `users.id` ON DELETE CASCADE
- When user deleted, all products deleted automatically

### Related Tables (for context)

**Products Table:**
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,        -- Foreign key to users
    name TEXT NOT NULL,
    description TEXT,
    quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
)
```

---

## 4. Existing Role/Permission Infrastructure

### Current State: NONE

The system has **NO role-based access control (RBAC)** currently implemented.

**What Exists:**
- Basic authentication (login/register)
- Session management via Flask-Login
- Route protection via @login_required decorator
- User-product ownership validation

**What's Missing:**
- User role field (admin/user/etc)
- Permission checking functions
- Role enforcement decorators
- Admin routes or admin panel
- Permission inheritance
- Sharing/collaboration system

### Access Control Pattern (Current)

All route protections follow this pattern:

```python
@inventory_bp.route('/product/<int:product_id>')
@login_required
def view_product(product_id):
    product = Product.get_by_id(product_id, ...)
    
    # Manual ownership check - MUST be explicit
    if not product or product.user_id != current_user.id:
        flash('Product not found.', 'error')
        return redirect(url_for('inventory.dashboard'))
    
    return render_template('inventory/product_detail.html', product=...)
```

**Issues:**
- Manual ownership checks on every route
- No admin override capability
- No sharing mechanism
- Error messages leak information (can't distinguish "product doesn't exist" from "not authorized")

---

## 5. Recommendations for Admin & Sharing Features

### Phase 1: Add Role-Based Access Control

**1A. Extend User Model**

Add to users table:
```sql
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';
-- Values: 'admin', 'user'

ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1;
-- For disabling accounts
```

Add to User class (models/user.py):
- `role` property
- `is_admin` property
- `set_role(role)` method
- Update `get_by_id()` and `get_by_email()` to load role

**1B. Create Permission Decorators**

New file: `decorators/auth.py`
```python
from functools import wraps
from flask import abort, current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def owner_or_admin(product_id_param='product_id'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            product_id = kwargs.get(product_id_param)
            product = Product.get_by_id(product_id)
            
            if not product:
                abort(404)
            
            if current_user.id != product.user_id and current_user.role != 'admin':
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### Phase 2: Add Product Sharing Infrastructure

**2A. Create Sharing Table**

```sql
CREATE TABLE product_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    shared_with_user_id INTEGER NOT NULL,
    permission_level TEXT DEFAULT 'view',  -- 'view', 'edit', 'admin'
    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    FOREIGN KEY (shared_with_user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE(product_id, shared_with_user_id)
)
```

**2B. Add Sharing Methods to Product Model**

```python
def share_with_user(user_id, permission_level='view'):
    """Share product with another user"""
    
def get_shared_users(self):
    """Get list of users this product is shared with"""
    
def check_access(user_id, permission_level='view'):
    """Check if user has access to product"""
    
@staticmethod
def get_shared_products(user_id):
    """Get products shared with user"""
```

**2C. Create Sharing Routes**

New file: `routes/sharing.py`
```python
@sharing_bp.route('/product/<product_id>/share', methods=['POST'])
def share_product(product_id):
    # Verify ownership
    # Share with email or user_id
    # Set permission level

@sharing_bp.route('/product/<product_id>/shares', methods=['GET'])
def view_shares(product_id):
    # List who product is shared with

@sharing_bp.route('/product/<product_id>/unshare/<user_id>', methods=['POST'])
def unshare_product(product_id, user_id):
    # Remove access for user
```

### Phase 3: Create Admin Panel

**3A. Admin Routes** (routes/admin.py)

```python
@admin_bp.route('/admin/users')
@admin_required
def manage_users():
    # List all users
    # View user details
    # Edit roles
    # Deactivate users

@admin_bp.route('/admin/users/<user_id>/role', methods=['POST'])
@admin_required
def set_user_role(user_id):
    # Change user role

@admin_bp.route('/admin/stats')
@admin_required
def admin_dashboard():
    # System statistics
    # User count
    # Product count
    # Storage usage
```

**3B. Admin Templates**

- templates/admin/dashboard.html
- templates/admin/users.html
- templates/admin/user_detail.html

### Phase 4: Update Existing Routes

**4A. Refactor Access Checks**

Replace manual ownership checks with decorator:

```python
# Before:
@inventory_bp.route('/product/<int:product_id>')
@login_required
def view_product(product_id):
    product = Product.get_by_id(product_id)
    if not product or product.user_id != current_user.id:
        abort(404)

# After:
@inventory_bp.route('/product/<int:product_id>')
@login_required
@owner_or_admin('product_id')
def view_product(product_id):
    product = Product.get_by_id(product_id)
    # Already verified ownership or admin status
```

**4B. Update Product Retrieval**

Modify queries to include shared products:
```python
@staticmethod
def get_user_accessible_products(user_id):
    """Get own products + shared products"""
    # Query products WHERE user_id = user_id
    # UNION with shared products
```

---

## 6. Implementation Priority

### Quick Wins (1-2 hours)
1. Add role field to users table
2. Create admin_required decorator
3. Create basic admin panel route
4. Add admin user manually to database

### Foundation (3-4 hours)
1. Refactor Product access checks to use decorators
2. Create sharing table
3. Add sharing methods to Product model
4. Create basic sharing UI

### Full Implementation (5-6 hours)
1. Complete sharing routes with validation
2. Admin user management interface
3. Permission level checks (view/edit/admin)
4. Sharing permissions UI on product detail

---

## 7. File Structure for Changes

```
inventory-app/
├── models/
│   ├── user.py                    [UPDATE: Add role, is_admin]
│   └── product.py                 [UPDATE: Add sharing methods]
├── routes/
│   ├── auth.py                    [NO CHANGE - works as-is]
│   ├── admin.py                   [NEW: Admin management]
│   ├── sharing.py                 [NEW: Product sharing]
│   └── inventory.py               [UPDATE: Use decorators]
├── decorators/
│   ├── __init__.py                [NEW]
│   └── auth.py                    [NEW: Decorators]
├── templates/
│   ├── admin/                     [NEW: Admin templates]
│   │   ├── dashboard.html
│   │   └── users.html
│   ├── sharing/                   [NEW: Sharing templates]
│   │   └── share_modal.html
│   └── inventory/                 [UPDATE: Add share button]
└── database.py                    [UPDATE: Migration support]
```

---

## 8. Security Considerations

### Current Strengths
- Password hashing with werkzeug (bcrypt)
- Session-based auth with HttpOnly cookies
- CSRF protection via SameSite
- Foreign key constraints for data integrity
- Input validation on email and password

### Current Weaknesses
- No role-based access control
- No sharing mechanism
- No audit logging
- No API rate limiting
- Ownership checks are manual (easy to forget)

### For New Features
- Validate all permission checks on server-side
- Never trust client-side role/permission claims
- Log sharing actions for audit trail
- Implement permission inheritance properly
- Use parametrized queries (already done, good!)

