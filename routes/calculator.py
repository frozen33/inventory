"""
Calculator routes for tile calculations and bill management
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from models.calculator import TileCalculator, FLOOR_TILES, WALL_TILES, calculate_custom_coverage
from models.calculation_bill import CalculationBill
from models.calculation_bill_item import CalculationBillItem
from models.product import Product
from models.tile_details import TileDetails


calculator_bp = Blueprint('calculator', __name__, url_prefix='/calculator')


@calculator_bp.route('/')
@login_required
def calculator_page():
    """Main calculator page with 3 sub-tabs"""
    # Get current session bill
    bill_items = session.get('current_bill', [])

    # Get all tiles from inventory for dropdown
    tiles_products = Product.get_all(product_type='tiles')
    tiles_with_details = []

    for product in tiles_products:
        tile_details_obj = product.get_tile_details()
        pricing = product.get_pricing()

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

    return render_template('calculator/calculator.html',
                         bill_items=bill_items,
                         tiles_inventory=tiles_with_details,
                         floor_tiles=FLOOR_TILES,
                         wall_tiles=WALL_TILES)


@calculator_bp.route('/calculate-floor', methods=['POST'])
@login_required
def calculate_floor():
    """Calculate floor tile requirements"""
    try:
        data = request.json

        # Check dimension mode: dimensions or direct square feet
        dimension_mode = data.get('dimension_mode', 'dimensions')

        if dimension_mode == 'sqfeet':
            # Direct square feet input
            area = float(data.get('total_sqfeet'))
            room_dimensions = f"{area} sq ft (direct)"
        else:
            # Calculate from width and length
            room_width = float(data.get('room_width'))
            room_length = float(data.get('room_length'))
            area = room_width * room_length
            room_dimensions = f"{room_width}x{room_length} ft"

        # Determine source type and get tile info
        source_type = data.get('source_type')  # 'predefined', 'inventory', 'manual'

        calculator = TileCalculator()

        if source_type == 'predefined':
            tile_size = data.get('tile_size')
            price_per_box = float(data.get('price_per_box')) if data.get('price_per_box') else None

            if dimension_mode == 'sqfeet':
                result = calculator.calculate_floor_boxes_from_area(area, tile_size=tile_size)
            else:
                result = calculator.calculate_floor_boxes(room_width, room_length, tile_size=tile_size)

            tile_name = f"Predefined {tile_size} ft"
            dimensions = f"{tile_size} ft"
            product_id = None

        elif source_type == 'inventory':
            product_id = int(data.get('product_id'))
            product = Product.get_by_id(product_id)
            tile_details = product.get_tile_details()
            pricing = product.get_pricing()

            tiles_per_box = tile_details['tiles_per_box']
            coverage_per_box = tile_details['sq_feet_per_box']

            if dimension_mode == 'sqfeet':
                result = calculator.calculate_floor_boxes_from_area(
                    area,
                    tiles_per_box=tiles_per_box,
                    coverage_per_box=coverage_per_box
                )
            else:
                result = calculator.calculate_floor_boxes(
                    room_width, room_length,
                    tiles_per_box=tiles_per_box,
                    coverage_per_box=coverage_per_box
                )

            tile_name = product.name
            dimensions = tile_details['dimension_display']
            price_per_box = pricing.get('selling_price') if pricing else None

        elif source_type == 'manual':
            tile_length = float(data.get('tile_length'))
            tile_width = float(data.get('tile_width'))
            tile_unit = data.get('tile_unit')  # 'feet' or 'inch'
            tiles_per_box = int(data.get('tiles_per_box'))
            price_per_box = float(data.get('price_per_box')) if data.get('price_per_box') else None

            # Calculate coverage
            coverage_per_box = calculate_custom_coverage(tile_length, tile_width, tile_unit, tiles_per_box)

            if dimension_mode == 'sqfeet':
                result = calculator.calculate_floor_boxes_from_area(
                    area,
                    tiles_per_box=tiles_per_box,
                    coverage_per_box=coverage_per_box
                )
            else:
                result = calculator.calculate_floor_boxes(
                    room_width, room_length,
                    tiles_per_box=tiles_per_box,
                    coverage_per_box=coverage_per_box
                )

            tile_name = "Manual Entry"
            dimensions = f"{tile_length}x{tile_width} {tile_unit}"
            product_id = None
        else:
            return jsonify({'error': 'Invalid source type'}), 400

        # Calculate total price if price provided
        total_price = None
        if price_per_box:
            total_price = price_per_box * result['boxes_needed']

        # Add metadata for bill
        result['source_type'] = source_type
        result['tile_name'] = tile_name
        result['dimensions'] = dimensions
        result['product_id'] = product_id
        result['room_dimensions'] = room_dimensions
        result['area_calculated'] = result['area']
        result['price_per_box'] = price_per_box
        result['total_price'] = total_price
        result['calculation_type'] = 'floor'

        return jsonify({'success': True, 'result': result})

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Calculation error: {str(e)}'}), 500


@calculator_bp.route('/calculate-wall', methods=['POST'])
@login_required
def calculate_wall():
    """Calculate wall tile requirements"""
    try:
        data = request.json

        # Check dimension mode: dimensions or direct square feet
        dimension_mode = data.get('dimension_mode', 'dimensions')
        deduct_door = data.get('deduct_door', True)

        if dimension_mode == 'sqfeet':
            # Direct square feet input
            wall_area = float(data.get('total_sqfeet'))
            # If user wants to deduct door from pre-calculated area
            if deduct_door:
                wall_area = wall_area - 21  # Standard door area
            room_dimensions = f"{wall_area} sq ft (direct)"
        else:
            # Calculate from width, length, and height
            room_width = float(data.get('room_width'))
            room_length = float(data.get('room_length'))
            room_height = float(data.get('room_height'))
            room_dimensions = f"{room_width}x{room_length}x{room_height} ft"
            wall_area = None  # Will be calculated by calculator

        # Determine source type and get tile info
        source_type = data.get('source_type')

        calculator = TileCalculator()

        if source_type == 'predefined':
            tile_size = data.get('tile_size')
            price_per_box = float(data.get('price_per_box')) if data.get('price_per_box') else None

            if dimension_mode == 'sqfeet':
                result = calculator.calculate_wall_boxes_from_area(
                    wall_area, tile_size=tile_size, deduct_door=deduct_door
                )
            else:
                result = calculator.calculate_wall_boxes(
                    room_width, room_length, room_height,
                    tile_size=tile_size, deduct_door=deduct_door
                )

            tile_name = f"Predefined {tile_size} inch"
            dimensions = f"{tile_size} inch"
            product_id = None

        elif source_type == 'inventory':
            product_id = int(data.get('product_id'))
            product = Product.get_by_id(product_id)
            tile_details = product.get_tile_details()
            pricing = product.get_pricing()

            tiles_per_box = tile_details['tiles_per_box']
            coverage_per_box = tile_details['sq_feet_per_box']

            if dimension_mode == 'sqfeet':
                result = calculator.calculate_wall_boxes_from_area(
                    wall_area,
                    tiles_per_box=tiles_per_box,
                    coverage_per_box=coverage_per_box,
                    deduct_door=deduct_door
                )
            else:
                result = calculator.calculate_wall_boxes(
                    room_width, room_length, room_height,
                    tiles_per_box=tiles_per_box,
                    coverage_per_box=coverage_per_box,
                    deduct_door=deduct_door
                )

            tile_name = product.name
            dimensions = tile_details['dimension_display']
            price_per_box = pricing.get('selling_price') if pricing else None

        elif source_type == 'manual':
            tile_length = float(data.get('tile_length'))
            tile_width = float(data.get('tile_width'))
            tile_unit = data.get('tile_unit')
            tiles_per_box = int(data.get('tiles_per_box'))
            price_per_box = float(data.get('price_per_box')) if data.get('price_per_box') else None

            coverage_per_box = calculate_custom_coverage(tile_length, tile_width, tile_unit, tiles_per_box)

            if dimension_mode == 'sqfeet':
                result = calculator.calculate_wall_boxes_from_area(
                    wall_area,
                    tiles_per_box=tiles_per_box,
                    coverage_per_box=coverage_per_box,
                    deduct_door=deduct_door
                )
            else:
                result = calculator.calculate_wall_boxes(
                    room_width, room_length, room_height,
                    tiles_per_box=tiles_per_box,
                    coverage_per_box=coverage_per_box,
                    deduct_door=deduct_door
                )

            tile_name = "Manual Entry"
            dimensions = f"{tile_length}x{tile_width} {tile_unit}"
            product_id = None
        else:
            return jsonify({'error': 'Invalid source type'}), 400

        # Calculate total price
        total_price = None
        if price_per_box:
            total_price = price_per_box * result['boxes_needed']

        # Add metadata
        result['source_type'] = source_type
        result['tile_name'] = tile_name
        result['dimensions'] = dimensions
        result['product_id'] = product_id
        result['room_dimensions'] = room_dimensions
        result['area_calculated'] = result['wall_area']
        result['price_per_box'] = price_per_box
        result['total_price'] = total_price
        result['calculation_type'] = 'wall'

        return jsonify({'success': True, 'result': result})

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Calculation error: {str(e)}'}), 500


@calculator_bp.route('/add-to-bill', methods=['POST'])
@login_required
def add_to_bill():
    """Add calculation result to session bill"""
    try:
        calculation = request.json

        # Get current bill from session
        if 'current_bill' not in session:
            session['current_bill'] = []

        # Add item to bill
        session['current_bill'].append(calculation)
        session.modified = True

        return jsonify({'success': True, 'bill_count': len(session['current_bill'])})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@calculator_bp.route('/remove-from-bill/<int:index>', methods=['POST'])
@login_required
def remove_from_bill(index):
    """Remove item from session bill by index"""
    try:
        if 'current_bill' in session and 0 <= index < len(session['current_bill']):
            session['current_bill'].pop(index)
            session.modified = True
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Invalid index'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@calculator_bp.route('/clear-bill', methods=['POST'])
@login_required
def clear_bill():
    """Clear the entire session bill"""
    try:
        session['current_bill'] = []
        session.modified = True
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@calculator_bp.route('/save-bill', methods=['POST'])
@login_required
def save_bill():
    """Save session bill to database"""
    try:
        bill_items = session.get('current_bill', [])

        if not bill_items:
            return jsonify({'error': 'No items in bill'}), 400

        # Create bill
        bill_id = CalculationBill.create(
            user_id=current_user.id,
            created_by=current_user.email,
            bill_name=request.json.get('bill_name')
        )

        # Add all items
        total_boxes = 0
        total_price = 0.0

        for item in bill_items:
            CalculationBillItem.create(bill_id, item)
            total_boxes += item.get('boxes_needed', 0)
            if item.get('total_price'):
                total_price += item['total_price']

        # Update bill totals
        CalculationBill.update_totals(bill_id, total_boxes, total_price)

        # Clear session bill
        session['current_bill'] = []
        session.modified = True

        return jsonify({'success': True, 'bill_id': bill_id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@calculator_bp.route('/bill-history')
@login_required
def bill_history():
    """Show all saved bills"""
    # Get all bills (shared view)
    bills = CalculationBill.get_all()

    # Get count of old bills
    old_bills_count = CalculationBill.get_count_older_than_days(30)

    return render_template('calculator/bill_history.html',
                         bills=bills,
                         old_bills_count=old_bills_count)


@calculator_bp.route('/bill/<int:bill_id>')
@login_required
def view_bill(bill_id):
    """View a specific bill with all items"""
    bill = CalculationBill.get_by_id(bill_id)

    if not bill:
        return "Bill not found", 404

    items = CalculationBillItem.get_by_bill_id(bill_id)

    return render_template('calculator/bill_detail.html',
                         bill=bill,
                         items=items)


@calculator_bp.route('/delete-old-bills', methods=['POST'])
@login_required
def delete_old_bills():
    """Delete bills older than 30 days"""
    try:
        deleted_count = CalculationBill.delete_older_than_days(30)
        return jsonify({'success': True, 'deleted_count': deleted_count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@calculator_bp.route('/delete-bill/<int:bill_id>', methods=['POST'])
@login_required
def delete_bill(bill_id):
    """Delete a specific bill"""
    try:
        CalculationBill.delete(bill_id)
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
