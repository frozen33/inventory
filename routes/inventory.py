import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
from models.product import Product
from models.product_audit_log import ProductAuditLog

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
    """Main inventory dashboard - Collaborative mode with tabs (Power Tools, Tiles & Calculator)"""
    try:
        search_term = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        product_type = request.args.get('type', 'power_tools')  # default to power_tools
        per_page = 12  # Products per page

        # If calculator tab, get calculator data
        if product_type == 'calculator':
            from models.tile_details import TileDetails

            # Get current session bill
            bill_items = session.get('current_bill', [])

            # Get all tiles from inventory for dropdown
            tiles_products = Product.get_all(product_type='tiles', database_path=current_app.config['DATABASE_PATH'])
            tiles_with_details = []

            for product in tiles_products:
                tile_details_obj = product.get_tile_details(database_path=current_app.config['DATABASE_PATH'])
                pricing = product.get_pricing(database_path=current_app.config['DATABASE_PATH'])

                if tile_details_obj:
                    # Convert TileDetails object to dictionary
                    tile_details = tile_details_obj if isinstance(tile_details_obj, dict) else tile_details_obj.to_dict() if hasattr(tile_details_obj, 'to_dict') else {}

                    tiles_with_details.append({
                        'id': product.id,
                        'name': product.name,
                        'dimensions': tile_details.get('dimension_display', ''),
                        'tiles_per_box': tile_details.get('tiles_per_box'),
                        'sq_feet_per_box': tile_details.get('sq_feet_per_box'),
                        'dimension_length': tile_details.get('dimension_length'),
                        'dimension_width': tile_details.get('dimension_width'),
                        'dimension_unit': tile_details.get('dimension_unit'),
                        'price': pricing.get('selling_price') if pricing else None
                    })

            return render_template('inventory/dashboard.html',
                                 products=[],
                                 bill_items=bill_items,
                                 tiles_inventory=tiles_with_details,
                                 product_type=product_type,
                                 total_products=0,
                                 search_term='',
                                 current_page=1,
                                 total_pages=0,
                                 has_prev=False,
                                 has_next=False)

        # Normal inventory display (power_tools or tiles)
        offset = (page - 1) * per_page

        # Get ALL products filtered by type (collaborative inventory)
        products = Product.get_all(
            limit=per_page,
            offset=offset,
            search_term=search_term,
            product_type=product_type,
            database_path=current_app.config['DATABASE_PATH']
        )

        # Get total count for pagination
        total_products = Product.get_total_count(
            search_term=search_term,
            product_type=product_type,
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
                             total_products=total_products,
                             product_type=product_type,
                             bill_items=[],
                             tiles_inventory=[])

    except Exception as e:
        flash('Error loading dashboard. Please try again.', 'error')
        print(f"Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return render_template('inventory/dashboard.html',
                             products=[],
                             product_type='power_tools',
                             bill_items=[],
                             tiles_inventory=[],
                             total_products=0,
                             search_term='',
                             current_page=1,
                             total_pages=0,
                             has_prev=False,
                             has_next=False)

@inventory_bp.route('/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    """Create new product"""
    if request.method == 'POST':
        try:
            # Get form data
            product_type = request.form.get('product_type', 'power_tools')
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            quantity = request.form.get('quantity', '0')
            buying_price = request.form.get('buying_price')
            selling_price = request.form.get('selling_price')
            mrp = request.form.get('mrp')

            # Validation
            if not name:
                flash('Product name is required.', 'error')
                return render_template('inventory/product_form.html', product_type=product_type)

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

            quantity = safe_int(quantity) if product_type == 'power_tools' else 0
            buying_price = safe_float(buying_price)
            selling_price = safe_float(selling_price)
            mrp = safe_float(mrp) if product_type == 'power_tools' else None

            # Create product with creator tracking
            product = Product.create_product(
                user_id=current_user.id,
                name=name,
                description=description,
                quantity=quantity,
                created_by=current_user.id,
                product_type=product_type,
                database_path=current_app.config['DATABASE_PATH']
            )

            # Log product creation
            ProductAuditLog.log_create(
                product_id=product.id,
                user_id=current_user.id,
                product_name=name,
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

            # If tiles product, create tile details
            if product_type == 'tiles':
                from models.tile_details import TileDetails

                tiles_per_box = safe_int(request.form.get('tiles_per_box', '0'))
                number_of_boxes = safe_int(request.form.get('number_of_boxes', '0'))
                dimension_length = safe_float(request.form.get('dimension_length'))
                dimension_width = safe_float(request.form.get('dimension_width'))
                dimension_unit = request.form.get('dimension_unit', 'feet')
                sq_feet_per_box = safe_float(request.form.get('sq_feet_per_box'))

                TileDetails.create(
                    product_id=product.id,
                    tiles_per_box=tiles_per_box,
                    number_of_boxes=number_of_boxes,
                    dimension_length=dimension_length,
                    dimension_width=dimension_width,
                    dimension_unit=dimension_unit,
                    sq_feet_per_box=sq_feet_per_box,
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

    # GET request - pass product_type from query params
    product_type = request.args.get('type', 'power_tools')
    return render_template('inventory/product_form.html', product_type=product_type)

@inventory_bp.route('/product/<int:product_id>')
@login_required
def view_product(product_id):
    """View single product - Collaborative mode (all users can view)"""
    try:
        product = Product.get_by_id(product_id, current_app.config['DATABASE_PATH'])

        if not product:
            flash('Product not found.', 'error')
            return redirect(url_for('inventory.dashboard'))

        product_dict = product.to_dict(database_path=current_app.config['DATABASE_PATH'])

        # Add creator and updater info
        product_dict['creator'] = product.get_creator_info(current_app.config['DATABASE_PATH'])
        product_dict['updater'] = product.get_updater_info(current_app.config['DATABASE_PATH'])

        return render_template('inventory/product_detail.html', product=product_dict)

    except Exception as e:
        flash('Error loading product. Please try again.', 'error')
        print(f"Product view error: {e}")
        return redirect(url_for('inventory.dashboard'))

@inventory_bp.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit existing product - Collaborative mode (all users can edit)"""
    try:
        product = Product.get_by_id(product_id, current_app.config['DATABASE_PATH'])

        if not product:
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

            # Track changes for audit log
            changes = {}
            old_pricing = product.get_pricing(current_app.config['DATABASE_PATH'])

            if name != product.name:
                changes['name'] = {'old': product.name, 'new': name}
            if description != product.description:
                changes['description'] = {'old': product.description, 'new': description}
            if quantity != product.quantity:
                changes['quantity'] = {'old': product.quantity, 'new': quantity}

            # Check pricing changes
            if old_pricing:
                if buying_price != old_pricing.get('buying_price'):
                    changes['buying_price'] = {'old': old_pricing.get('buying_price'), 'new': buying_price}
                if selling_price != old_pricing.get('selling_price'):
                    changes['selling_price'] = {'old': old_pricing.get('selling_price'), 'new': selling_price}
                if mrp != old_pricing.get('mrp'):
                    changes['mrp'] = {'old': old_pricing.get('mrp'), 'new': mrp}

            # Update product with updated_by tracking
            product.update(
                name=name,
                description=description,
                quantity=quantity,
                updated_by=current_user.id,
                database_path=current_app.config['DATABASE_PATH']
            )

            product.set_pricing(
                buying_price=buying_price,
                selling_price=selling_price,
                mrp=mrp,
                database_path=current_app.config['DATABASE_PATH']
            )

            # Update tile details if this is a tiles product
            if product.product_type == 'tiles':
                from models.tile_details import TileDetails

                tiles_per_box = safe_int(request.form.get('tiles_per_box', '0'))
                number_of_boxes = safe_int(request.form.get('number_of_boxes', '0'))
                dimension_length = safe_float(request.form.get('dimension_length'))
                dimension_width = safe_float(request.form.get('dimension_width'))
                dimension_unit = request.form.get('dimension_unit', 'feet')
                sq_feet_per_box = safe_float(request.form.get('sq_feet_per_box'))

                # Get existing tile details
                tile_details = TileDetails.get_by_product_id(product.id, current_app.config['DATABASE_PATH'])

                if tile_details:
                    # Update existing
                    tile_details.update(
                        tiles_per_box=tiles_per_box,
                        number_of_boxes=number_of_boxes,
                        dimension_length=dimension_length,
                        dimension_width=dimension_width,
                        dimension_unit=dimension_unit,
                        sq_feet_per_box=sq_feet_per_box,
                        database_path=current_app.config['DATABASE_PATH']
                    )
                else:
                    # Create new (shouldn't happen but handle gracefully)
                    TileDetails.create(
                        product_id=product.id,
                        tiles_per_box=tiles_per_box,
                        number_of_boxes=number_of_boxes,
                        dimension_length=dimension_length,
                        dimension_width=dimension_width,
                        dimension_unit=dimension_unit,
                        sq_feet_per_box=sq_feet_per_box,
                        database_path=current_app.config['DATABASE_PATH']
                    )

            # Log the update if there were changes
            if changes:
                ProductAuditLog.log_update(
                    product_id=product.id,
                    user_id=current_user.id,
                    product_name=name,
                    changes_dict=changes,
                    database_path=current_app.config['DATABASE_PATH']
                )

            flash(f'Product "{name}" updated successfully!', 'success')
            return redirect(url_for('inventory.view_product', product_id=product.id))

        product_dict = product.to_dict(database_path=current_app.config['DATABASE_PATH'])
        product_dict['product_type'] = product.product_type
        return render_template('inventory/product_form.html', product=product_dict, edit_mode=True, product_type=product.product_type)

    except Exception as e:
        flash('Error editing product. Please try again.', 'error')
        print(f"Product edit error: {e}")
        return redirect(url_for('inventory.dashboard'))

@inventory_bp.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete product - Collaborative mode (all users can delete)"""
    try:
        product = Product.get_by_id(product_id, current_app.config['DATABASE_PATH'])

        if not product:
            flash('Product not found.', 'error')
            return redirect(url_for('inventory.dashboard'))

        product_name = product.name

        # Log deletion BEFORE deleting (product_id will be set to NULL after deletion)
        ProductAuditLog.log_delete(
            product_id=product.id,
            user_id=current_user.id,
            product_name=product_name,
            database_path=current_app.config['DATABASE_PATH']
        )

        # Delete associated images from filesystem
        images = product.get_images(current_app.config['DATABASE_PATH'])
        user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products', f'user_{product.user_id}')

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
    """Search products (AJAX endpoint) - Collaborative mode"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))

        if not query:
            return jsonify({'products': []})

        # Search ALL products (collaborative inventory)
        products = Product.get_all(
            limit=limit,
            search_term=query,
            database_path=current_app.config['DATABASE_PATH']
        )

        # Convert to dictionary format
        results = []
        for product in products:
            product_dict = product.to_dict(database_path=current_app.config['DATABASE_PATH'])
            # Add creator info
            if hasattr(product, 'creator_email'):
                product_dict['creator_email'] = product.creator_email
            if hasattr(product, 'updater_email'):
                product_dict['updater_email'] = product.updater_email
            results.append(product_dict)

        return jsonify({'products': results})

    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': 'Search failed'}), 500