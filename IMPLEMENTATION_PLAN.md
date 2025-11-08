# Implementation Plan: Collaborative Shared Inventory System

**Date:** November 7, 2025
**Goal:** Convert from isolated user inventories to a shared collaborative workspace
**Estimated Time:** 6-7 hours

---

## 🎯 System Overview

### Current Behavior (Multi-Tenant)
```
User A logs in → Sees only THEIR products (isolated)
User B logs in → Sees only THEIR products (isolated)
```

### New Behavior (Collaborative)
```
User A logs in → Sees ALL products (collaborative)
User B logs in → Sees ALL products (collaborative)
Any user can add/edit/delete any product
Audit log tracks who did what
```

---

## 📊 Database Changes

### 1. Add `role` to users table
```sql
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';
CREATE INDEX idx_users_role ON users(role);
```

**Roles:**
- `user` - Regular user (default) - can add/edit/delete products
- `admin` - Administrator - can manage users + view audit logs

### 2. Create `product_audit_log` table
```sql
CREATE TABLE product_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,  -- NULL if product was deleted
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- 'create', 'update', 'delete'
    product_name TEXT,  -- Store name for deleted products
    changes TEXT,  -- JSON of what changed
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_audit_product_id ON product_audit_log(product_id);
CREATE INDEX idx_audit_user_id ON product_audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON product_audit_log(timestamp);
```

### 3. Add tracking fields to products table
```sql
ALTER TABLE products ADD COLUMN created_by INTEGER REFERENCES users(id);
ALTER TABLE products ADD COLUMN updated_by INTEGER REFERENCES users(id);
```

---

## 🔧 Implementation Phases

### Phase 1: Database Migration (1 hour)

**Files to create/modify:**
- `migrations/add_collaborative_features.py` - Migration script
- `scripts/manage_admin.py` - CLI tool for admin management

**Migration script should:**
1. Add `role` column to users
2. Create `product_audit_log` table
3. Add `created_by` and `updated_by` to products
4. Backfill existing products with their current owner as creator
5. Create first admin user (manual promotion)

**CLI tool commands:**
```bash
# Promote user to admin
python scripts/manage_admin.py promote test@example.com

# Demote admin to user
python scripts/manage_admin.py demote admin@example.com

# List all admins
python scripts/manage_admin.py list-admins

# Show all users
python scripts/manage_admin.py list-users
```

---

### Phase 2: Backend Models (2 hours)

#### 2.1 Update User Model (`models/user.py`)

**Add methods:**
```python
def is_admin(self):
    """Check if user is admin"""
    return self.role == 'admin'

@staticmethod
def get_all_users(database_path='inventory.db'):
    """Get all users (admin only)"""
    # Return list of all users with their product counts

@staticmethod
def promote_to_admin(user_id, database_path='inventory.db'):
    """Promote user to admin role"""

@staticmethod
def demote_from_admin(user_id, database_path='inventory.db'):
    """Demote user to regular user role"""
```

#### 2.2 Update Product Model (`models/product.py`)

**Replace:**
- `get_by_user()` → `get_all()` - Fetch all products regardless of user

**Add methods:**
```python
@staticmethod
def get_all(limit=None, offset=0, search_term='', database_path='inventory.db'):
    """Get all products for collaborative view"""
    # No user_id filter - everyone sees everything

def get_creator_name(database_path='inventory.db'):
    """Get name/email of user who created this product"""

def get_updater_name(database_path='inventory.db'):
    """Get name/email of user who last updated this product"""
```

**Update methods:**
- `create_product()` - Add `created_by` parameter
- `update_product()` - Add `updated_by` parameter
- `delete_product()` - Log deletion before deleting

#### 2.3 Create ProductAuditLog Model (`models/product_audit_log.py`)

**New file with methods:**
```python
class ProductAuditLog:
    @staticmethod
    def log_create(product_id, user_id, product_name, database_path):
        """Log product creation"""

    @staticmethod
    def log_update(product_id, user_id, changes, database_path):
        """Log product update with changes dict"""

    @staticmethod
    def log_delete(product_id, user_id, product_name, database_path):
        """Log product deletion"""

    @staticmethod
    def get_product_history(product_id, database_path):
        """Get all audit logs for a specific product"""

    @staticmethod
    def get_user_activity(user_id, limit=50, database_path):
        """Get recent activity by a user"""

    @staticmethod
    def get_recent_activity(limit=100, database_path):
        """Get recent activity across all products (admin only)"""
```

---

### Phase 3: Backend Routes (2 hours)

#### 3.1 Update Inventory Routes (`routes/inventory.py`)

**Changes needed:**

1. **Dashboard route** - Remove user filter
```python
@inventory_bp.route('/dashboard')
@login_required
def dashboard():
    # OLD: products = Product.get_by_user(user_id=current_user.id)
    # NEW: products = Product.get_all()
```

2. **Product detail/edit routes** - Remove ownership check
```python
# REMOVE these checks:
# if product.user_id != current_user.id:
#     abort(403)

# Everyone can edit any product now
```

3. **Add audit logging to all operations**
```python
# After creating product:
ProductAuditLog.log_create(product.id, current_user.id, product.name)

# After updating product:
changes = {'field': 'old_value -> new_value'}
ProductAuditLog.log_update(product.id, current_user.id, changes)

# Before deleting product:
ProductAuditLog.log_delete(product.id, current_user.id, product.name)
```

4. **Update product creation** - Track creator
```python
product = Product.create_product(
    created_by=current_user.id,  # NEW
    updated_by=current_user.id,  # NEW
    # ... other fields
)
```

#### 3.2 Create Admin Routes (`routes/admin.py`)

**New file with routes:**

```python
@admin_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard with system overview"""
    if not current_user.is_admin():
        abort(403)

    # Show: total users, total products, recent activity

@admin_bp.route('/admin/users')
@login_required
def list_users():
    """List all users with their activity"""
    if not current_user.is_admin():
        abort(403)

@admin_bp.route('/admin/users/<int:user_id>/promote', methods=['POST'])
@login_required
def promote_user(user_id):
    """Promote user to admin"""
    if not current_user.is_admin():
        abort(403)

@admin_bp.route('/admin/users/<int:user_id>/demote', methods=['POST'])
@login_required
def demote_user(user_id):
    """Demote admin to regular user"""
    if not current_user.is_admin():
        abort(403)

@admin_bp.route('/admin/audit-log')
@login_required
def audit_log():
    """View complete audit log"""
    if not current_user.is_admin():
        abort(403)

    # Show all activity with filters

@admin_bp.route('/admin/audit-log/product/<int:product_id>')
@login_required
def product_history(product_id):
    """View history for a specific product"""
    if not current_user.is_admin():
        abort(403)
```

---

### Phase 4: Frontend UI Updates (2 hours)

#### 4.1 Update Dashboard (`templates/inventory/dashboard.html`)

**Add to product cards:**
```html
<div class="product-meta">
    <small class="text-muted">
        Created by {{ product.creator_email }} on {{ product.created_at }}
    </small>
    <small class="text-muted">
        Last updated by {{ product.updater_email }} on {{ product.updated_at }}
    </small>
</div>
```

**Add admin badge to navbar** (if user is admin):
```html
{% if current_user.is_admin() %}
    <span class="badge badge-admin">Admin</span>
    <a href="{{ url_for('admin.admin_dashboard') }}">Admin Panel</a>
{% endif %}
```

#### 4.2 Create Admin Dashboard (`templates/admin/dashboard.html`)

**Sections:**
1. **System Overview**
   - Total users
   - Total products
   - Activity today/week/month

2. **User Management**
   - List all users
   - Show role (admin/user)
   - Promote/demote buttons

3. **Recent Activity**
   - Last 20 actions across all users
   - Filter by user/action type

#### 4.3 Create Audit Log Viewer (`templates/admin/audit_log.html`)

**Features:**
- Filterable table: by user, action, date range
- Show: timestamp, user, action, product, changes
- Link to product (if still exists)
- Export to CSV

#### 4.4 Update Product Detail Page (`templates/inventory/product.html`)

**Add "History" tab:**
- Show all changes to this product
- Who created it
- Who edited it (with what changes)
- Who deleted images, changed prices, etc.

#### 4.5 Update CSS (`static/css/style.css`)

**Add styles for:**
```css
.product-meta {
    /* Show creator/updater info */
}

.badge-admin {
    /* Admin badge styling */
}

.audit-log-table {
    /* Activity log table styling */
}

.action-create { color: green; }
.action-update { color: blue; }
.action-delete { color: red; }
```

---

### Phase 5: Testing (30 minutes)

**Test scenarios:**

1. **Basic Collaboration**
   - User A creates product
   - User B logs in and sees it
   - User B edits the product
   - User A sees the changes

2. **Audit Logging**
   - Create/edit/delete product
   - Check audit log shows correct user and timestamp
   - Verify deleted products still show in history

3. **Admin Functions**
   - Promote user to admin
   - Admin views all users
   - Admin views complete audit log
   - Demote admin back to user

4. **Edge Cases**
   - Multiple users editing simultaneously
   - Deleted products in audit log
   - User who created product is deleted

---

## 🗂️ File Structure (New/Modified)

```
inventory-app/
├── migrations/
│   └── add_collaborative_features.py  [NEW]
├── scripts/
│   └── manage_admin.py                [NEW]
├── models/
│   ├── user.py                        [MODIFIED]
│   ├── product.py                     [MODIFIED]
│   └── product_audit_log.py           [NEW]
├── routes/
│   ├── inventory.py                   [MODIFIED]
│   └── admin.py                       [NEW]
├── templates/
│   ├── inventory/
│   │   ├── dashboard.html             [MODIFIED]
│   │   └── product.html               [MODIFIED]
│   └── admin/
│       ├── dashboard.html             [NEW]
│       ├── users.html                 [NEW]
│       └── audit_log.html             [NEW]
├── static/
│   └── css/
│       └── style.css                  [MODIFIED]
└── app.py                             [MODIFIED - register admin blueprint]
```

---

## 🔐 Security Considerations

### What Changed:
- ❌ **Removed:** Per-user product isolation
- ✅ **Added:** Audit logging (accountability)
- ✅ **Added:** Admin role (user management)

### Security Notes:
- **All logged-in users can access all products** - This is intentional
- **Audit log is immutable** - Even admins can't delete history
- **Admin role required** for user management and audit viewing
- **First admin must be promoted manually** via CLI script

### Best Practices:
1. **Don't give login credentials to untrusted users** - they can modify anything
2. **Regularly review audit logs** - catch accidental/malicious changes
3. **Backup database regularly** - protect against accidental deletions
4. **Use strong passwords** - no product-level access control anymore

---

## 📋 Migration Steps (Production)

### Before Running Migration:

1. **Backup current database:**
   ```bash
   cp inventory.db inventory.db.backup.$(date +%Y%m%d)
   ```

2. **Backup uploads folder:**
   ```bash
   tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/
   ```

### Run Migration:

```bash
cd /home/nandhu/Pictures/Inventory/inventory-app
source ../envinven/bin/activate
python migrations/add_collaborative_features.py
```

### Post-Migration:

1. **Promote first admin:**
   ```bash
   python scripts/manage_admin.py promote test@example.com
   ```

2. **Verify migration:**
   ```bash
   python -c "from database import check_database; check_database()"
   ```

3. **Test application:**
   - Start server: `python app.py`
   - Login with two different users
   - Verify both see all products
   - Test create/edit/delete
   - Check audit log

---

## 📈 Success Metrics

After implementation, you should have:

✅ All users see the same product list
✅ Any user can add/edit/delete any product
✅ Complete audit trail of who did what
✅ Admin panel for user management
✅ Audit log viewer showing all activity
✅ Product history showing all changes
✅ Visual indicators of who created/modified products

---

## 🚀 Ready to Implement?

**Estimated breakdown:**
- Phase 1 (Database): 1 hour
- Phase 2 (Models): 2 hours
- Phase 3 (Routes): 2 hours
- Phase 4 (Frontend): 2 hours
- Phase 5 (Testing): 30 mins

**Total: ~7.5 hours**

Let me know and I'll start with Phase 1! 🎯
