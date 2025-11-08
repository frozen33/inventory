# Tiles Inventory - Remaining Implementation

## Status: 60% Complete

### ✅ Completed:
1. Database migration (product_type field + tiles_details table)
2. TileDetails model
3. Product model updated with tile support
4. Dashboard route updated to filter by type

### 🚧 Remaining Tasks:

---

## 1. Update `new_product` route (routes/inventory.py)

Add after line 105 (in the POST handler):

```python
# Get product type
product_type = request.form.get('product_type', 'power_tools')

# ... existing code for name, description, etc ...

# Create product with type
product = Product.create_product(
    user_id=current_user.id,
    name=name,
    description=description,
    quantity=quantity if product_type == 'power_tools' else 0,
    created_by=current_user.id,
    product_type=product_type,
    database_path=current_app.config['DATABASE_PATH']
)

# If tiles product, create tile details
if product_type == 'tiles':
    from models.tile_details import TileDetails

    tiles_per_box = int(request.form.get('tiles_per_box', 0))
    number_of_boxes = int(request.form.get('number_of_boxes', 0))
    dimension_length = float(request.form.get('dimension_length', 0))
    dimension_width = float(request.form.get('dimension_width', 0))
    dimension_unit = request.form.get('dimension_unit', 'feet')
    sq_feet_per_box = float(request.form.get('sq_feet_per_box', 0))

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
```

---

## 2. Update `edit_product` route

Similar changes to handle tile details updates.

---

## 3. Update Dashboard Template (templates/inventory/dashboard.html)

Add tabs before the search bar (around line 10):

```html
<!-- Product Type Tabs -->
<div style="margin-bottom: 2rem;">
    <div style="border-bottom: 2px solid #e2e8f0; display: flex; gap: 1rem;">
        <a href="{{ url_for('inventory.dashboard', type='power_tools') }}"
           style="padding: 1rem 2rem; text-decoration: none; font-weight: 600;
                  {% if product_type == 'power_tools' %}
                  border-bottom: 3px solid #3b82f6; color: #3b82f6;
                  {% else %}
                  color: #64748b;
                  {% endif %}">
            🔧 Power Tools & Others
        </a>
        <a href="{{ url_for('inventory.dashboard', type='tiles') }}"
           style="padding: 1rem 2rem; text-decoration: none; font-weight: 600;
                  {% if product_type == 'tiles' %}
                  border-bottom: 3px solid #3b82f6; color: #3b82f6;
                  {% else %}
                  color: #64748b;
                  {% endif %}">
            🔲 Tiles
        </a>
    </div>
</div>
```

---

## 4. Create Tile Product Form (templates/inventory/tile_form.html)

```html
{% extends "base.html" %}

{% block title %}{% if edit_mode %}Edit{% else %}Add{% endif %} Tile Product{% endblock %}

{% block content %}
<h1>{% if edit_mode %}Edit{% else %}Add{% endif %} Tile Product</h1>

<form method="POST" enctype="multipart/form-data">
    <input type="hidden" name="product_type" value="tiles">

    <!-- Name -->
    <div class="form-group">
        <label class="form-label">Product Name *</label>
        <input type="text" name="name" class="form-input" required
               value="{{ product.name if edit_mode else '' }}">
    </div>

    <!-- Description -->
    <div class="form-group">
        <label class="form-label">Description</label>
        <textarea name="description" class="form-input form-textarea">{{ product.description if edit_mode else '' }}</textarea>
    </div>

    <!-- Pricing (NO MRP for tiles) -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div class="form-group">
            <label class="form-label">Buying Price</label>
            <input type="number" step="0.01" name="buying_price" class="form-input"
                   value="{{ product.pricing.buying_price if edit_mode and product.pricing else '' }}">
        </div>
        <div class="form-group">
            <label class="form-label">Selling Price</label>
            <input type="number" step="0.01" name="selling_price" class="form-input"
                   value="{{ product.pricing.selling_price if edit_mode and product.pricing else '' }}">
        </div>
    </div>

    <!-- Tile-specific fields -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div class="form-group">
            <label class="form-label">Tiles per Box</label>
            <input type="number" name="tiles_per_box" class="form-input"
                   value="{{ product.tile_details.tiles_per_box if edit_mode and product.tile_details else '' }}">
        </div>
        <div class="form-group">
            <label class="form-label">Number of Boxes</label>
            <input type="number" name="number_of_boxes" class="form-input"
                   value="{{ product.tile_details.number_of_boxes if edit_mode and product.tile_details else '' }}">
        </div>
    </div>

    <!-- Tile Dimensions -->
    <div class="form-group">
        <label class="form-label">Tile Dimensions</label>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
            <input type="number" step="0.01" name="dimension_length" class="form-input" placeholder="Length"
                   value="{{ product.tile_details.dimension_length if edit_mode and product.tile_details else '' }}">
            <input type="number" step="0.01" name="dimension_width" class="form-input" placeholder="Width"
                   value="{{ product.tile_details.dimension_width if edit_mode and product.tile_details else '' }}">
            <select name="dimension_unit" class="form-input">
                <option value="feet" {% if edit_mode and product.tile_details and product.tile_details.dimension_unit == 'feet' %}selected{% endif %}>Feet</option>
                <option value="inch" {% if edit_mode and product.tile_details and product.tile_details.dimension_unit == 'inch' %}selected{% endif %}>Inch</option>
            </select>
        </div>
    </div>

    <!-- Sq Feet per Box -->
    <div class="form-group">
        <label class="form-label">Sq Feet per Box</label>
        <input type="number" step="0.01" name="sq_feet_per_box" class="form-input"
               value="{{ product.tile_details.sq_feet_per_box if edit_mode and product.tile_details else '' }}">
    </div>

    <!-- Images -->
    <div class="form-group">
        <label class="form-label">Product Images</label>
        <input type="file" name="images" multiple accept="image/*" class="form-input">
    </div>

    <button type="submit" class="btn btn-primary">
        {% if edit_mode %}Update{% else %}Add{% endif %} Tile Product
    </button>
</form>
{% endblock %}
```

---

## 5. Update Add Product Button

In dashboard template, update the "Add Product" link to have a dropdown for selecting type.

Or create two separate links:
- "Add Power Tool/Other"
- "Add Tile Product"

---

## Quick Start Instructions:

1. The database is already migrated ✓
2. Models are ready ✓
3. Update routes as shown above
4. Update templates
5. Test by adding a tile product

---

## Testing:

```bash
# Start the app
python app.py

# Go to http://localhost:5000
# Login
# Click "Tiles" tab
# Add a tile product with dimensions
```

