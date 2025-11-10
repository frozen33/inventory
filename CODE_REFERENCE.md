# Code Reference: Authentication System

## File Locations

All authentication-related files are in:
```
/home/nandhu/Pictures/Inventory/inventory-app/
├── models/user.py (151 lines)
├── routes/auth.py (172 lines)
├── app.py (135 lines) - Lines 15-26 for Flask-Login setup
├── config.py (83 lines) - Lines 18-27 for session config
└── database.py (184 lines) - Lines 29-37 for users table schema
```

---

## Key Code Snippets

### 1. User Model - Key Methods

**Password Validation (models/user.py:84-86)**
```python
def check_password(self, password):
    """Check if provided password matches hash"""
    return check_password_hash(self.password_hash, password)
```
Uses werkzeug's secure comparison - prevents timing attacks.

**User Retrieval for Login (models/user.py:62-82)**
```python
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
            return User(...)
        return None
    finally:
        conn.close()
```
Note: Parameterized query (?) prevents SQL injection.

**Session-Based User Loading (app.py:22-25)**
```python
@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.get_by_id(int(user_id), app.config['DATABASE_PATH'])
```
Called by Flask-Login on every request to restore user from session.

### 2. Authentication Routes - Key Flows

**Login Route (routes/auth.py:24-64)**
```python
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('inventory.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        # Validation
        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('auth/login.html', email=email)

        if not validate_email(email):
            flash('Please provide a valid email address.', 'error')
            return render_template('auth/login.html', email=email)

        # Try to find user
        try:
            user = User.get_by_email(email)

            if user and user.check_password(password):
                login_user(user, remember=remember)
                flash(f'Welcome back, {user.email}!', 'success')

                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('inventory.dashboard'))
            else:
                flash('Invalid email or password.', 'error')

        except Exception as e:
            flash('An error occurred during login. Please try again.', 'error')
            print(f"Login error: {e}")

    return render_template('auth/login.html')
```

Key features:
- Generic error message (doesn't reveal if email exists)
- Email normalized to lowercase
- Remembering login option
- Redirect to 'next' page after login
- Exception handling

**Registration Route (routes/auth.py:66-115)**
```python
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('inventory.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not email or not password or not confirm_password:
            flash('Please fill in all fields.', 'error')
            return render_template('auth/register.html', email=email)

        if not validate_email(email):
            flash('Please provide a valid email address.', 'error')
            return render_template('auth/register.html', email=email)

        is_valid, password_message = validate_password(password)
        if not is_valid:
            flash(password_message, 'error')
            return render_template('auth/register.html', email=email)

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html', email=email)

        # Check if user already exists
        try:
            if User.email_exists(email):
                flash('An account with this email already exists.', 'error')
                return render_template('auth/register.html', email=email)

            # Create new user
            user = User.create_user(email, password)

            if user:
                login_user(user)
                flash(f'Account created successfully! Welcome, {user.email}!', 'success')
                return redirect(url_for('inventory.dashboard'))
            else:
                flash('Failed to create account. Please try again.', 'error')

        except Exception as e:
            flash('An error occurred during registration. Please try again.', 'error')
            print(f"Registration error: {e}")

    return render_template('auth/register.html')
```

Key features:
- Email format validation before DB check
- Password strength validation
- Duplicate email check
- Auto-login after registration
- Multiple validation layers

### 3. Password Validation (routes/auth.py:14-22)

```python
def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"

    if len(password) > 128:
        return False, "Password must be less than 128 characters"

    return True, "Password is valid"
```

Rules:
- Minimum 6 characters (sensible minimum)
- Maximum 128 characters (prevents DoS)
- Could add complexity rules if needed

### 4. Email Validation (routes/auth.py:9-12)

```python
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
```

Validates:
- Standard email format
- Domain with extension
- No spaces
- Valid characters

### 5. Database Access Pattern (models/user.py:38-59)

```python
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
```

Best practices shown:
- Use parameters (?) not f-strings
- Proper connection cleanup (finally block)
- Row factory for named access
- Error handling implicit (exceptions bubble up)

### 6. Product Access Control Example (routes/inventory.py:187-204)

```python
@inventory_bp.route('/product/<int:product_id>')
@login_required
def view_product(product_id):
    """View single product"""
    try:
        product = Product.get_by_id(product_id, current_app.config['DATABASE_PATH'])

        # Manual ownership check
        if not product or product.user_id != current_user.id:
            flash('Product not found.', 'error')
            return redirect(url_for('inventory.dashboard'))

        product_dict = product.to_dict(database_path=current_app.config['DATABASE_PATH'])
        return render_template('inventory/product_detail.html', product=product_dict)

    except Exception as e:
        flash('Error loading product. Please try again.', 'error')
        print(f"Product view error: {e}")
        return redirect(url_for('inventory.dashboard'))
```

Current approach:
- @login_required ensures authenticated
- Manual check: product.user_id != current_user.id
- Returns generic "not found" error
- Would benefit from @owner_required decorator

### 7. Session Configuration (config.py:18-27)

```python
# Session configuration
PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Remember me for 7 days
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Flask-Login configuration
REMEMBER_COOKIE_DURATION = timedelta(days=7)
REMEMBER_COOKIE_SECURE = False  # Set to True in production
REMEMBER_COOKIE_HTTPONLY = True
```

Details:
- 7-day session cookie lifetime
- HttpOnly flag prevents JavaScript access
- SameSite Lax prevents CSRF
- Set SECURE=True in production (requires HTTPS)

---

## Database Schema Details

### Users Table (database.py:30-37)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

Index created (database.py:82):
```sql
CREATE INDEX idx_users_email ON users(email)
```

Constraints:
- id: Auto-increment, cannot be null
- email: Unique (no duplicate emails), cannot be null
- password_hash: Bcrypt hash format, cannot be null
- created_at: Auto-set timestamp

### Foreign Keys (database.py:49)

```sql
FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
```

Effect:
- When user is deleted, all their products deleted automatically
- Maintains data consistency
- Prevents orphaned product records

---

## Route Structure

### Authentication Routes (routes/auth.py)

All routes prefixed with `/auth`:

```
GET/POST  /auth/login              → login()
GET/POST  /auth/register           → register()
GET/POST  /auth/logout             → logout()
GET/POST  /auth/profile            → profile()
GET/POST  /auth/change-password    → change_password()
```

Protection:
- login, register: Accessible only if NOT authenticated
- logout, profile, change-password: Require @login_required

### Inventory Routes (routes/inventory.py)

All routes prefixed with `/inventory`:

```
GET       /inventory/dashboard                    → dashboard()
GET/POST  /inventory/product/new                  → new_product()
GET       /inventory/product/<product_id>         → view_product()
GET/POST  /inventory/product/<product_id>/edit    → edit_product()
POST      /inventory/product/<product_id>/delete  → delete_product()
GET       /inventory/uploads/<path:filename>      → uploaded_file()
GET       /inventory/search                       → search()
```

All protected with @login_required + manual ownership check

### Main Routes (app.py)

```
GET  /             → index() - Redirect to dashboard or login
GET  /dashboard    → dashboard() - Redirect to inventory.dashboard
```

---

## Security Analysis by Component

### Password Handling
Location: models/user.py
- Storage: werkzeug.security.generate_password_hash (bcrypt)
- Comparison: werkzeug.security.check_password_hash
- Strength: 6-128 characters
- Status: SECURE

### Session Management
Location: app.py, config.py
- Method: Flask-Login with database backend
- Storage: HttpOnly cookies
- CSRF: SameSite Lax
- Duration: 7 days
- Status: SECURE

### Input Validation
Location: routes/auth.py
- Email: Regex validation
- Password: Length checks
- Form data: Stripped and normalized
- Status: GOOD (could add rate limiting)

### Database Access
Location: All models
- SQL: Parameterized queries (prevents injection)
- Connections: Properly closed in finally blocks
- Foreign keys: Enabled with cascade delete
- Status: SECURE

### Access Control
Location: routes/inventory.py
- Method: Manual ownership checks
- Pattern: Fragile, easy to forget
- Issue: Information leak (404 vs 403)
- Recommendation: Use decorators
- Status: NEEDS IMPROVEMENT

---

## Testing Commands

```bash
# Activate virtual environment
cd /home/nandhu/Pictures/Inventory
source envinven/bin/activate
cd inventory-app

# Start application
python3 app.py

# Default test user
# Email: test@example.com
# Password: testpass123

# Test in browser
# http://localhost:5000/auth/login
# http://localhost:5000/auth/register
```

---

## Next Steps for Enhancement

1. **Implement role decorators**
   - Location: Create decorators/auth.py
   - Adds @admin_required, @owner_required decorators

2. **Add role field to users**
   - Location: Modify database.py schema
   - Add: role TEXT DEFAULT 'user'

3. **Create sharing infrastructure**
   - Location: Create product_shares table
   - Add sharing methods to Product model

4. **Replace manual checks**
   - Location: Update routes/inventory.py
   - Use decorators instead of if statements

5. **Build admin panel**
   - Location: Create routes/admin.py
   - Routes for user management, stats, etc.

See AUTH_ANALYSIS.md for detailed implementation guide.
