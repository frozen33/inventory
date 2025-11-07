import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
from models.product import Product

inventory_bp = Blueprint('inventory', __name__)

def allowed_file(filename):
    """Check if file type is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def generate_unique_filename(filename):
    """Generate unique filename to prevent conflicts"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
    return f"{uuid.uuid4().hex}.{ext}"

def create_user_upload_dir(user_id):
    """Create user-specific upload directory"""
    user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products', f'user_{user_id}')
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def resize_image(image_path, max_width=1200, max_height=1200, quality=85):
    """Resize and optimize image"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Calculate new size maintaining aspect ratio
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Save optimized image
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
            return True
    except Exception as e:
        print(f"Error resizing image: {e}")
        return False

@inventory_bp.route('/dashboard')
@login_required
def dashboard():
    """Main inventory dashboard"""
    try:
        search_term = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 12  # Products per page

        offset = (page - 1) * per_page

        # Get products for current user
        products = Product.get_by_user(
            user_id=current_user.id,
            limit=per_page,
            offset=offset,
            search_term=search_term,
            database_path=current_app.config['DATABASE_PATH']
        )

        # Get total count for pagination
        total_products = Product.get_user_product_count(
            user_id=current_user.id,
            database_path=current_app.config['DATABASE_PATH']
        )

        # Calculate pagination info
        total_pages = (total_products + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages

        # Enhance products with full data
        enhanced_products = []
        for product in products:
            product_dict = product.to_dict(database_path=current_app.config['DATABASE_PATH'])
            enhanced_products.append(product_dict)

        return render_template('inventory/dashboard.html',
                             products=enhanced_products,
                             search_term=search_term,
                             current_page=page,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next,
                             total_products=total_products)

    except Exception as e:
        flash('Error loading dashboard. Please try again.', 'error')
        print(f"Dashboard error: {e}")
        return render_template('inventory/dashboard.html', products=[])

@inventory_bp.route('/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    """Create new product"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            quantity = request.form.get('quantity', '0')
            buying_price = request.form.get('buying_price')
            selling_price = request.form.get('selling_price')
            mrp = request.form.get('mrp')

            # Validation
            if not name:
                flash('Product name is required.', 'error')
                return render_template('inventory/product_form.html')

            # Convert values
            def safe_float(value):
                try:
                    return float(value) if value and value.strip() else None
                except:
                    return None

            def safe_int(value):
                try:
                    return int(value) if value and str(value).strip() else 0
                except:
                    return 0

            quantity = safe_int(quantity)
            buying_price = safe_float(buying_price)
            selling_price = safe_float(selling_price)
            mrp = safe_float(mrp)

            # Create product
            product = Product.create_product(
                user_id=current_user.id,
                name=name,
                description=description,
                quantity=quantity,
                database_path=current_app.config['DATABASE_PATH']
            )

            # Set pricing if provided
            if any([buying_price, selling_price, mrp]):
                product.set_pricing(
                    buying_price=buying_price,
                    selling_price=selling_price,
                    mrp=mrp,
                    database_path=current_app.config['DATABASE_PATH']
                )

            # Handle file uploads
            uploaded_files = request.files.getlist('images')
            if uploaded_files and uploaded_files[0].filename:
                user_dir = create_user_upload_dir(current_user.id)

                for file in uploaded_files:
                    if file and allowed_file(file.filename):
                        # Generate unique filename
                        unique_filename = generate_unique_filename(file.filename)
                        file_path = os.path.join(user_dir, unique_filename)

                        # Save file
                        file.save(file_path)

                        # Resize and optimize
                        if resize_image(file_path):
                            # Add to database
                            product.add_image(
                                filename=unique_filename,
                                original_name=secure_filename(file.filename),
                                database_path=current_app.config['DATABASE_PATH']
                            )
                        else:
                            # Remove file if resize failed
                            os.remove(file_path)
                            flash(f'Failed to process image: {file.filename}', 'warning')

            flash(f'Product "{name}" created successfully!', 'success')
            return redirect(url_for('inventory.view_product', product_id=product.id))

        except Exception as e:
            flash('Error creating product. Please try again.', 'error')
            print(f"Product creation error: {e}")

    return render_template('inventory/product_form.html')

@inventory_bp.route('/product/<int:product_id>')
@login_required
def view_product(product_id):
    """View single product"""
    try:
        product = Product.get_by_id(product_id, current_app.config['DATABASE_PATH'])

        if not product or product.user_id != current_user.id:
            flash('Product not found.', 'error')
            return redirect(url_for('inventory.dashboard'))

        product_dict = product.to_dict(database_path=current_app.config['DATABASE_PATH'])
        return render_template('inventory/product_detail.html', product=product_dict)

    except Exception as e:
        flash('Error loading product. Please try again.', 'error')
        print(f"Product view error: {e}")
        return redirect(url_for('inventory.dashboard'))

@inventory_bp.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit existing product"""
    try:
        product = Product.get_by_id(product_id, current_app.config['DATABASE_PATH'])

        if not product or product.user_id != current_user.id:
            flash('Product not found.', 'error')
            return redirect(url_for('inventory.dashboard'))

        if request.method == 'POST':
            # Get form data
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            quantity = request.form.get('quantity', '0')
            buying_price = request.form.get('buying_price')
            selling_price = request.form.get('selling_price')
            mrp = request.form.get('mrp')

            # Validation
            if not name:
                flash('Product name is required.', 'error')
                return render_template('inventory/product_form.html',
                                     product=product.to_dict(database_path=current_app.config['DATABASE_PATH']),
                                     edit_mode=True)

            # Convert values
            def safe_float(value):
                try:
                    return float(value) if value and value.strip() else None
                except:
                    return None

            def safe_int(value):
                try:
                    return int(value) if value and str(value).strip() else 0
                except:
                    return 0

            quantity = safe_int(quantity)
            buying_price = safe_float(buying_price)
            selling_price = safe_float(selling_price)
            mrp = safe_float(mrp)

            # Update product
            product.update(name=name, description=description, quantity=quantity, database_path=current_app.config['DATABASE_PATH'])

            product.set_pricing(
                buying_price=buying_price,
                selling_price=selling_price,
                mrp=mrp,
                database_path=current_app.config['DATABASE_PATH']
            )

            flash(f'Product "{name}" updated successfully!', 'success')
            return redirect(url_for('inventory.view_product', product_id=product.id))

        product_dict = product.to_dict(database_path=current_app.config['DATABASE_PATH'])
        return render_template('inventory/product_form.html', product=product_dict, edit_mode=True)

    except Exception as e:
        flash('Error editing product. Please try again.', 'error')
        print(f"Product edit error: {e}")
        return redirect(url_for('inventory.dashboard'))

@inventory_bp.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete product"""
    try:
        product = Product.get_by_id(product_id, current_app.config['DATABASE_PATH'])

        if not product or product.user_id != current_user.id:
            flash('Product not found.', 'error')
            return redirect(url_for('inventory.dashboard'))

        product_name = product.name

        # Delete associated images from filesystem
        images = product.get_images(current_app.config['DATABASE_PATH'])
        user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products', f'user_{current_user.id}')

        for image in images:
            file_path = os.path.join(user_dir, image['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)

        # Delete product (cascade will handle database cleanup)
        product.delete(current_app.config['DATABASE_PATH'])

        flash(f'Product "{product_name}" deleted successfully.', 'success')

    except Exception as e:
        flash('Error deleting product. Please try again.', 'error')
        print(f"Product deletion error: {e}")

    return redirect(url_for('inventory.dashboard'))

@inventory_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    # Extract user directory from filename path
    if '/' in filename:
        user_folder, file_name = filename.split('/', 1)
        user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products', user_folder)
        return send_from_directory(user_dir, file_name)
    else:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@inventory_bp.route('/search')
@login_required
def search():
    """Search products (AJAX endpoint)"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))

        if not query:
            return jsonify({'products': []})

        products = Product.get_by_user(
            user_id=current_user.id,
            limit=limit,
            search_term=query,
            database_path=current_app.config['DATABASE_PATH']
        )

        # Convert to dictionary format
        results = []
        for product in products:
            product_dict = product.to_dict(database_path=current_app.config['DATABASE_PATH'])
            results.append(product_dict)

        return jsonify({'products': results})

    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': 'Search failed'}), 500