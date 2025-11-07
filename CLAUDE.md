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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
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
```

## Key Features

### Authentication
- [x] User registration/login
- [x] Session-based authentication
- [x] Protected routes (no access without login)
- [x] Password hashing (werkzeug)

### Product Management
- [x] Add/edit/delete products
- [x] Product name and description
- [x] Multiple image uploads per product
- [x] Three price fields: buying_price, selling_price, mrp
- [x] Product listing with search/filter

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

## File Structure

```
inventory/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── database.py          # Database initialization
├── models/
│   ├── __init__.py
│   ├── user.py          # User model
│   └── product.py       # Product model
├── routes/
│   ├── __init__.py
│   ├── auth.py          # Authentication routes
│   └── inventory.py     # Product management routes
├── static/
│   ├── css/
│   │   └── style.css    # Main stylesheet
│   ├── js/
│   │   └── app.js       # Frontend JavaScript
│   └── images/          # Static images
├── templates/
│   ├── base.html        # Base template
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   ├── dashboard.html   # Main inventory view
│   └── product.html     # Product details/edit
├── uploads/             # User uploaded images
└── inventory.db         # SQLite database file
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

### Phase 1: Core Setup ⏳
- [ ] Project structure
- [ ] Database initialization
- [ ] Basic Flask app

### Phase 2: Authentication 🔄
- [ ] User registration/login
- [ ] Session management
- [ ] Route protection

### Phase 3: Product Management 📋
- [ ] CRUD operations
- [ ] Image upload
- [ ] Price management

### Phase 4: Frontend 🎨
- [ ] Responsive design
- [ ] Mobile optimization
- [ ] User experience

### Phase 5: Testing & Deployment 🚀
- [ ] Cross-platform testing
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
*Last Updated: 2025-09-21*
*Environment: Ubuntu 22.04 VM → Debian 12 32-bit*