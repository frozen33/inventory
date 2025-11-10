# Visual Summary: Auth System Architecture

## Current User Data Model

```
┌─────────────────────────────────────┐
│          USERS TABLE                │
├─────────────────────────────────────┤
│ id (PK)                   INT       │  ← Auto-increment
│ email (UNIQUE)            TEXT      │  ← Login identifier
│ password_hash             TEXT      │  ← Bcrypt hash
│ created_at (DEFAULT)      TIMESTAMP │  ← Account creation
└─────────────────────────────────────┘
         ↓
    Index: idx_users_email
    (Fast lookup by email)
```

## User Object Structure (Python)

```
User (Flask-Login UserMixin)
├── Properties (from DB)
│   ├── id
│   ├── email
│   ├── password_hash (never exposed)
│   └── created_at
├── Properties (inherited from UserMixin)
│   ├── is_authenticated = True/False
│   ├── is_active = True
│   └── is_anonymous = False
└── Methods
    ├── check_password(pwd) → bool
    ├── update_password(new_pwd) → bool
    ├── get_product_count() → int
    ├── to_dict() → {id, email, created_at, product_count}
    └── (static) create_user(email, pwd) → User
    └── (static) get_by_id(id) → User
    └── (static) get_by_email(email) → User
    └── (static) email_exists(email) → bool
```

## Authentication Flow Diagram

```
REGISTRATION PATH
─────────────────
User fills form → validate inputs → check email exists?
                                       ├─ YES → error
                                       └─ NO → hash password
                                              → insert user
                                              → login
                                              → dashboard

LOGIN PATH
──────────
User fills form → validate format → lookup by email
                                       ├─ NOT FOUND → error
                                       └─ FOUND → check password
                                                  ├─ INVALID → error
                                                  └─ VALID → login
                                                            → set remember cookie
                                                            → redirect next page

SESSION MANAGEMENT
───────────────────
Flask-Login Manager
├── User loader: get_by_id()
├── Login view: /auth/login
├── Session TTL: 7 days
├── Remember cookie: 7 days
├── HttpOnly: True (no JS access)
└── SameSite: Lax (CSRF protection)

LOGOUT
──────
Current user → clear session → redirect to login
```

## Current Access Control

```
ROUTE PROTECTION LAYERS
───────────────────────

Layer 1: @login_required
├─ Check: Is user logged in?
├─ Success: Continue to route
└─ Failure: Redirect to login

Layer 2: Manual Ownership Check (in route handler)
├─ Get resource (product)
├─ Check: Is product.user_id == current_user.id?
├─ Success: Return resource
└─ Failure: Redirect to dashboard with error

EXAMPLE CODE:
─────────────
@inventory_bp.route('/product/<int:product_id>')
@login_required                          ← Layer 1
def view_product(product_id):
    product = Product.get_by_id(...)
    
    # Layer 2 - Manual check
    if not product or product.user_id != current_user.id:
        flash('Product not found.', 'error')
        return redirect(url_for('inventory.dashboard'))
    
    return render_template(...)
```

## Database Relationships

```
┌──────────────────┐
│  USERS (4 cols)  │
│  ┌────────────┐  │
│  │ id (PK)    │  │
│  │ email      │  │
│  │ password.. │  │
│  │ created_at │  │
│  └────────────┘  │
└──────────────────┘
         ↑
         │ 1:N
         │
┌──────────────────────────────┐
│  PRODUCTS (7 cols)           │
│  ┌──────────────────────┐    │
│  │ id (PK)              │    │
│  │ user_id (FK)◄────────┼────┘
│  │ name                 │
│  │ description          │
│  │ quantity             │
│  │ created_at           │
│  │ updated_at           │
│  └──────────────────────┘
└──────────────────────────────┘
         ↑
         │ 1:N (CASCADE DELETE)
         │
┌────────────────────────────────────────┐
│  PRODUCT_IMAGES & PRODUCT_PRICING      │
└────────────────────────────────────────┘
```

## What's Missing for Admin & Sharing

```
MISSING INFRASTRUCTURE
──────────────────────

1. ROLES
   users table needs:
   ├── role TEXT DEFAULT 'user'  ← 'admin' or 'user'
   └── is_active BOOLEAN DEFAULT 1

2. PERMISSIONS
   No decorator pattern for:
   ├── @admin_required
   ├── @owner_required
   └── @owner_or_admin

3. SHARING
   No table for:
   ├── product_shares (product ↔ user mapping)
   └── No sharing methods in Product model

4. AUDIT
   No table for:
   ├── action_logs
   └── No tracking of sharing changes

5. ADMIN ROUTES
   None exist:
   ├── /admin/dashboard
   ├── /admin/users
   └── /admin/stats

COMPARISON: Simple vs Full RBAC
───────────────────────────────

Simple (Current)
├─ Only "users"
├─ Manual checks everywhere
├─ Hard to add features
└─ Error-prone

Full RBAC (Recommended)
├─ Users + Roles
├─ Decorators enforce access
├─ Easy to add features
├─ Consistent enforcement
└─ Sharing built-in
```

## Implementation Roadmap

```
PHASE 1: Roles (1-2 hours)
┌────────────────────────────────┐
│ 1. ALTER users table           │
│    └─ Add: role, is_active     │
│ 2. Update User model           │
│    └─ Load role from DB        │
│ 3. Create decorators/auth.py   │
│    └─ @admin_required          │
│ 4. Create basic admin route    │
│    └─ /admin/dashboard         │
└────────────────────────────────┘

PHASE 2: Sharing Foundation (3-4 hours)
┌────────────────────────────────┐
│ 1. Create product_shares table │
│ 2. Add sharing methods to      │
│    Product model               │
│ 3. Create sharing routes       │
│ 4. Simple sharing UI           │
└────────────────────────────────┘

PHASE 3: Full Features (5-6 hours)
┌────────────────────────────────┐
│ 1. Permission level system     │
│    └─ view/edit/admin          │
│ 2. Admin user management       │
│ 3. Audit logging               │
│ 4. Complete UI/UX              │
└────────────────────────────────┘

PHASE 4: Refactor (2-3 hours)
┌────────────────────────────────┐
│ 1. Replace manual checks with  │
│    decorators                  │
│ 2. Include shared products in  │
│    queries                     │
│ 3. Add comprehensive tests     │
└────────────────────────────────┘
```

## Key Files Reference

```
Authentication Files:
├── models/user.py           ← User model, auth methods
├── routes/auth.py           ← Login/Register/Logout
├── app.py                   ← Flask-Login setup
└── config.py                ← Session config

Database:
├── database.py              ← Schema initialization
└── inventory.db             ← SQLite file

Product Management:
├── models/product.py        ← Product model
└── routes/inventory.py      ← CRUD routes
                             ← (Access control needed here)

FUTURE Files:
├── decorators/auth.py       ← NEW: Role decorators
├── routes/admin.py          ← NEW: Admin management
├── routes/sharing.py        ← NEW: Product sharing
└── models/share.py          ← NEW: Sharing model
```

## Security Audit Results

```
GOOD ✓
├─ Password hashing (werkzeug/bcrypt)
├─ HttpOnly session cookies
├─ SameSite cookie flag
├─ Email format validation
├─ Password strength requirements
├─ Unique email constraint
├─ Foreign key constraints
├─ Parameterized SQL queries
└─ Cascade delete on user deletion

NEEDS IMPROVEMENT ⚠
├─ No role-based access control
├─ Manual ownership checks (easy to forget)
├─ No audit logging
├─ No API rate limiting
├─ No sharing mechanism
├─ No admin override capability
└─ Information leak in 404 vs 403 errors

RECOMMENDED ★
├─ Implement decorator-based access control
├─ Add role field to users
├─ Create sharing infrastructure
├─ Log security-relevant actions
├─ Add request rate limiting
└─ Improve error messages
```
