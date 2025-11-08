# Inventory Management System

## Project Overview
A web-based inventory management system with user authentication, designed for both mobile and desktop views. The system allows users to manage products with images, descriptions, and pricing information.

## Architecture

### Local-First Design
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │◄──►│   Python Flask   │◄──►│   SQLite DB     │
│ HTML/CSS/JS     │    │   Backend API    │    │   Local File    │
│ (Responsive)    │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Local Storage   │
                       │  Product Images  │
                       │                  │
                       └──────────────────┘
```

### Remote Access (When Needed)
```
Internet ◄─► Cloudflare Tunnel ◄─► Local Flask App
                (temp URL)
```

## Tech Stack

### Backend
- **Language**: Python 3.8+ (compatible with 32-bit)
- **Framework**: Flask (lightweight)
- **Database**: SQLite3 (file-based, no server)
- **Authentication**: Flask-Login + werkzeug password hashing
- **File Upload**: Native Python (no external deps)

### Frontend
- **HTML5** with semantic markup
- **CSS3** with Flexbox/Grid (responsive design)
- **Vanilla JavaScript** (no frameworks)
- **Mobile-first** responsive design

### Storage
- **Database**: Single SQLite file (`inventory.db`)
- **Images**: Local filesystem (`/uploads/` directory)
- **Sessions**: Flask built-in session management

## System Requirements

### Minimum Hardware
- **RAM**: 512MB (will use ~100MB)
- **Storage**: 1GB free space
- **CPU**: Any 32-bit or 64-bit x86 processor
- **Network**: Optional (for remote access)

### Software Requirements
- **OS**: Linux (Debian 12, Ubuntu 22.04+)
- **Python**: 3.8 or higher
- **Browser**: Any modern browser (Chrome, Firefox, Safari)

### Compatibility Matrix
| Environment | Status | Notes |
|-------------|--------|--------|
| Ubuntu 22.04 VM (Intel i5) | ✅ Primary Dev | Current environment |
| Debian 12 (32-bit Atom) | ✅ Production | Target deployment |
| Windows 10/11 | ✅ Compatible | For development |
| macOS | ✅ Compatible | For development |

## Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    quantity INTEGER DEFAULT 0,
    product_type TEXT DEFAULT 'power_tools',
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (created_by) REFERENCES users (id),
    FOREIGN KEY (updated_by) REFERENCES users (id)
);

-- Product images table
CREATE TABLE product_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    original_name TEXT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);

-- Product pricing table
CREATE TABLE product_pricing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER UNIQUE NOT NULL,
    buying_price DECIMAL(10,2),
    selling_price DECIMAL(10,2),
    mrp DECIMAL(10,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);

-- Audit log table
CREATE TABLE product_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    product_name TEXT,
    changes TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Tiles details table
CREATE TABLE tiles_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER UNIQUE NOT NULL,
    tiles_per_box INTEGER,
    number_of_boxes INTEGER,
    dimension_length DECIMAL(10,2),
    dimension_width DECIMAL(10,2),
    dimension_unit TEXT DEFAULT 'feet',
    sq_feet_per_box DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);
```

## Key Features

### Authentication
- [x] User registration/login
- [x] Session-based authentication
- [x] Protected routes (no access without login)
- [x] Password hashing (werkzeug)
- [x] Admin role system

### Product Management
- [x] Add/edit/delete products
- [x] Product name and description
- [x] Multiple image uploads per product
- [x] Three price fields: buying_price, selling_price, mrp
- [x] Product listing with search/filter
- [x] **Dual product types:**
  - **Power Tools & Others:** Traditional inventory with quantity and MRP
  - **Tiles:** Specialized fields (tiles/box, dimensions, sq feet/box)
- [x] Tabbed dashboard interface for product type separation

### Collaborative Features
- [x] All users can view all products
- [x] All users can add/edit/delete any product
- [x] Audit logging tracks who created/modified what
- [x] Creator and updater attribution displayed

### Admin Features
- [x] User management (promote/demote admins)
- [x] Complete audit log viewing
- [x] System statistics dashboard
- [x] User activity tracking

### Responsive Design
- [x] Mobile-first CSS design
- [x] Touch-friendly interfaces
- [x] Optimized for screens 320px-1920px
- [x] Progressive enhancement

### Image Handling
- [x] Local file storage
- [x] Image validation (size, type)
- [x] Automatic image optimization
- [x] Secure file naming
- [x] Per-user upload directories

## File Structure

```
inventory-app/
├── app.py                        # Main Flask application
├── config.py                     # Configuration settings
├── requirements.txt              # Python dependencies
├── database.py                   # Database initialization
├── inventory.db                  # SQLite database file
├── CLAUDE.md                     # Project documentation (this file)
├── SESSION_PROGRESS.md           # Latest session summary
├── TILES_FEATURE_COMPLETE.md     # Tiles feature documentation
├── models/
│   ├── __init__.py
│   ├── user.py                   # User model (with admin support)
│   ├── product.py                # Product model (with product_type)
│   ├── product_audit_log.py      # Audit logging model
│   └── tile_details.py           # Tile details model
├── routes/
│   ├── __init__.py
│   ├── auth.py                   # Authentication routes
│   ├── inventory.py              # Product management routes
│   └── admin.py                  # Admin panel routes
├── migrations/
│   ├── add_collaborative_features.py  # Collaborative + admin migration
│   └── add_tiles_inventory.py         # Tiles feature migration
├── scripts/
│   └── manage_admin.py           # Admin management CLI
├── static/
│   ├── css/
│   │   └── style.css             # Main stylesheet
│   ├── js/
│   │   └── app.js                # Frontend JavaScript
│   └── images/                   # Static images
├── templates/
│   ├── base.html                 # Base template (with admin nav)
│   ├── auth/
│   │   ├── login.html            # Login page
│   │   └── register.html         # Registration page
│   ├── inventory/
│   │   ├── dashboard.html        # Tabbed inventory dashboard
│   │   ├── product_form.html     # Dynamic product form
│   │   └── product_detail.html   # Product detail view
│   └── admin/
│       ├── dashboard.html        # Admin dashboard
│       ├── users.html            # User management
│       └── audit_log.html        # Audit log viewer
└── uploads/
    └── products/
        └── user_1/               # Per-user image directories
```

## Deployment Options

### Local Development (Current)
```bash
# Ubuntu 22.04 VM
cd /home/nandhu/Pictures/Inventory
source envinven/bin/activate
cd inventory-app
python3 app.py
# Access: http://localhost:5000
```

### Production (Debian 32-bit Server)
```bash
# Debian 12 server
cd /path/to/inventory
python3 app.py
# Access: http://192.168.x.x:5000
```

### Remote Access (Temporary)
```bash
# Install cloudflared
sudo apt install cloudflared
# Create tunnel
cloudflared tunnel --url http://localhost:5000
# Share generated URL: https://random-name.trycloudflare.com
```

## Development Phases

### Phase 1: Core Setup ✅
- [x] Project structure
- [x] Database initialization
- [x] Basic Flask app

### Phase 2: Authentication ✅
- [x] User registration/login
- [x] Session management
- [x] Route protection

### Phase 3: Product Management ✅
- [x] CRUD operations
- [x] Image upload
- [x] Price management

### Phase 4: Frontend ✅
- [x] Responsive design
- [x] Mobile optimization
- [x] User experience

### Phase 5: Advanced Features ✅
- [x] Collaborative inventory (all users see all products)
- [x] Admin role system
- [x] Audit logging
- [x] Dual product types (Power Tools & Tiles)
- [x] Tabbed dashboard interface

### Phase 6: Testing & Deployment 🔄
- [x] Cross-platform testing
- [ ] Performance optimization
- [ ] Production deployment

## Commands to Remember

### Development
```bash
# Activate virtual environment
source ../envinven/bin/activate

# Start development server
python3 app.py

# Install dependencies
pip install -r requirements.txt

# Database reset
python3 -c "from database import init_db; init_db()"
```

### Testing
```bash
# Test on different ports
python3 app.py --port 3000

# Test mobile view
# Use browser dev tools responsive mode
```

### Deployment
```bash
# Check Python version
python3 --version

# Check system architecture
uname -a

# Share temporarily
cloudflared tunnel --url http://localhost:5000
```

## Notes & Considerations

### Performance Optimizations
- SQLite with WAL mode for better concurrency
- Image compression for uploads
- CSS/JS minification for production
- Lazy loading for product images

### Security Measures
- CSRF protection
- File upload validation
- SQL injection prevention (SQLite parameterized queries)
- Secure session management
- Input sanitization

### Maintenance
- Regular database backups
- Log rotation
- Image cleanup for deleted products
- Performance monitoring

---

## Recent Updates (November 7, 2025)

### Tiles Inventory Feature ✅
- Added dual product type system (Power Tools & Tiles)
- Created tabbed dashboard interface
- Implemented tile-specific fields with dimension unit dropdown
- All tile fields are user input (no auto-calculation)
- See `TILES_FEATURE_COMPLETE.md` for full details

### Current Database State
- 2 users (test@example.com + another)
- 5 products (4 power tools, 1 tile)
- 2 images uploaded
- 4 audit log entries
- Collaborative mode active

### Testing Status
- ✅ Tiles feature fully tested
- ✅ Product creation working for both types
- ✅ Tab switching functional
- ✅ Image uploads working
- ✅ All CRUD operations verified

---
*Last Updated: 2025-11-07*
*Environment: Ubuntu 22.04 VM → Debian 12 32-bit*
*Latest Feature: Tiles Inventory System*