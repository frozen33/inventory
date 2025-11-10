// Calculator JavaScript
// Global variables to store calculation results
let floorCalculationResult = null;
let wallCalculationResult = null;

// Switch between calculator tabs
function switchCalculatorTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Mark button as active
    event.target.classList.add('active');

    // Update bill if on bill tab
    if (tabName === 'bill') {
        updateBillDisplay();
    }
}

// Switch floor input mode
function switchFloorMode(mode) {
    document.getElementById('floor-predefined').style.display = mode === 'predefined' ? 'block' : 'none';
    document.getElementById('floor-inventory').style.display = mode === 'inventory' ? 'block' : 'none';
    document.getElementById('floor-manual').style.display = mode === 'manual' ? 'block' : 'none';
}

// Switch wall input mode
function switchWallMode(mode) {
    document.getElementById('wall-predefined').style.display = mode === 'predefined' ? 'block' : 'none';
    document.getElementById('wall-inventory').style.display = mode === 'inventory' ? 'block' : 'none';
    document.getElementById('wall-manual').style.display = mode === 'manual' ? 'block' : 'none';
}

// Floor calculation form handler
document.getElementById('floor-calc-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const mode = document.querySelector('input[name="floor_mode"]:checked').value;
    const dimensionMode = document.querySelector('input[name="floor_dimension_mode"]:checked').value;

    // Build request data
    const data = {
        source_type: mode,
        dimension_mode: dimensionMode
    };

    // Add dimension data based on mode
    if (dimensionMode === 'dimensions') {
        data.room_width = formData.get('room_width');
        data.room_length = formData.get('room_length');
    } else {
        data.total_sqfeet = formData.get('total_sqfeet');
    }

    if (mode === 'predefined') {
        data.tile_size = formData.get('tile_size');
        data.price_per_box = formData.get('price_per_box_pred') || null;
    } else if (mode === 'inventory') {
        data.product_id = formData.get('product_id');
    } else if (mode === 'manual') {
        data.tile_length = formData.get('tile_length');
        data.tile_width = formData.get('tile_width');
        data.tile_unit = formData.get('tile_unit');
        data.tiles_per_box = formData.get('tiles_per_box_manual');
        data.price_per_box = formData.get('price_per_box_manual') || null;
    }

    try {
        const response = await fetch('/calculator/calculate-floor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            floorCalculationResult = result.result;
            displayFloorResults(result.result);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Calculation failed: ' + error.message);
    }
});

// Display floor results
function displayFloorResults(result) {
    document.getElementById('floor-area').textContent = `${result.area} sq ft`;
    document.getElementById('floor-coverage').textContent = `${result.coverage_per_box} sq ft/box`;
    document.getElementById('floor-boxes').textContent = `${result.boxes_exact} → ${result.boxes_needed} boxes`;

    if (result.price_per_box) {
        document.getElementById('floor-price-row').style.display = 'flex';
        document.getElementById('floor-total-price').textContent = `₹${result.total_price.toFixed(2)}`;
    } else {
        document.getElementById('floor-price-row').style.display = 'none';
    }

    document.getElementById('floor-results').style.display = 'block';
}

// Wall calculation form handler
document.getElementById('wall-calc-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const mode = document.querySelector('input[name="wall_mode"]:checked').value;
    const dimensionMode = document.querySelector('input[name="wall_dimension_mode"]:checked').value;

    const data = {
        source_type: mode,
        dimension_mode: dimensionMode,
        deduct_door: formData.get('deduct_door') === 'on'
    };

    // Add dimension data based on mode
    if (dimensionMode === 'dimensions') {
        data.room_width = formData.get('room_width');
        data.room_length = formData.get('room_length');
        data.room_height = formData.get('room_height');
    } else {
        data.total_sqfeet = formData.get('total_sqfeet');
    }

    if (mode === 'predefined') {
        data.tile_size = formData.get('tile_size');
        data.price_per_box = formData.get('price_per_box_pred') || null;
    } else if (mode === 'inventory') {
        data.product_id = formData.get('product_id');
    } else if (mode === 'manual') {
        data.tile_length = formData.get('tile_length');
        data.tile_width = formData.get('tile_width');
        data.tile_unit = formData.get('tile_unit');
        data.tiles_per_box = formData.get('tiles_per_box_manual');
        data.price_per_box = formData.get('price_per_box_manual') || null;
    }

    try {
        const response = await fetch('/calculator/calculate-wall', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            wallCalculationResult = result.result;
            displayWallResults(result.result);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Calculation failed: ' + error.message);
    }
});

// Display wall results
function displayWallResults(result) {
    document.getElementById('wall-perimeter').textContent = `${result.perimeter} ft`;
    document.getElementById('wall-area').textContent = `${result.wall_area} sq ft`;
    document.getElementById('wall-coverage').textContent = `${result.coverage_per_box} sq ft/box`;
    document.getElementById('wall-boxes').textContent = `${result.boxes_exact} → ${result.boxes_needed} boxes`;

    if (result.price_per_box) {
        document.getElementById('wall-price-row').style.display = 'flex';
        document.getElementById('wall-total-price').textContent = `₹${result.total_price.toFixed(2)}`;
    } else {
        document.getElementById('wall-price-row').style.display = 'none';
    }

    document.getElementById('wall-results').style.display = 'block';
}

// Add floor calculation to bill
async function addFloorToBill() {
    if (!floorCalculationResult) {
        alert('Please calculate first');
        return;
    }

    try {
        const response = await fetch('/calculator/add-to-bill', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(floorCalculationResult)
        });

        const result = await response.json();

        if (result.success) {
            alert('Added to bill!');
            // Reload page to show updated bill and switch to bill tab
            window.location.href = '/inventory/dashboard?type=calculator&show_bill=1';
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Failed to add to bill: ' + error.message);
    }
}

// Add wall calculation to bill
async function addWallToBill() {
    if (!wallCalculationResult) {
        alert('Please calculate first');
        return;
    }

    try {
        const response = await fetch('/calculator/add-to-bill', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(wallCalculationResult)
        });

        const result = await response.json();

        if (result.success) {
            alert('Added to bill!');
            // Reload page to show updated bill and switch to bill tab
            window.location.href = '/inventory/dashboard?type=calculator&show_bill=1';
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Failed to add to bill: ' + error.message);
    }
}

// Remove item from bill
async function removeFromBill(index) {
    if (!confirm('Remove this item from bill?')) {
        return;
    }

    try {
        const response = await fetch(`/calculator/remove-from-bill/${index}`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            location.reload();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Failed to remove item: ' + error.message);
    }
}

// Clear entire bill
async function clearBill() {
    if (!confirm('Clear all items from bill?')) {
        return;
    }

    try {
        const response = await fetch('/calculator/clear-bill', {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            location.reload();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Failed to clear bill: ' + error.message);
    }
}

// Save bill to database
async function saveBill() {
    const billName = prompt('Enter a name for this bill (optional):');

    try {
        const response = await fetch('/calculator/save-bill', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ bill_name: billName })
        });

        const result = await response.json();

        if (result.success) {
            alert('Bill saved successfully!');
            location.reload();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Failed to save bill: ' + error.message);
    }
}

// Update bill count badge
function updateBillCount(count) {
    document.getElementById('bill-count-badge').textContent = count;
}

// Update bill display and summary
function updateBillDisplay() {
    const rows = document.querySelectorAll('#bill-items-tbody tr');

    let totalBoxes = 0;
    let totalPrice = 0;
    let floorBoxes = 0;
    let floorPrice = 0;
    let wallBoxes = 0;
    let wallPrice = 0;

    rows.forEach(row => {
        const type = row.querySelector('.badge').textContent.trim().toLowerCase();
        const boxesCell = row.cells[4].textContent;
        const boxes = parseInt(boxesCell.match(/→\s*(\d+)/)[1]);
        const priceCell = row.cells[6].textContent;
        const price = priceCell !== '-' ? parseFloat(priceCell.replace('₹', '')) : 0;

        totalBoxes += boxes;
        totalPrice += price;

        if (type === 'floor') {
            floorBoxes += boxes;
            floorPrice += price;
        } else if (type === 'wall') {
            wallBoxes += boxes;
            wallPrice += price;
        }
    });

    const summaryHtml = `
        <p><strong>Floor Tiles:</strong> ${floorBoxes} boxes ${floorPrice > 0 ? '(₹' + floorPrice.toFixed(2) + ')' : ''}</p>
        <p><strong>Wall Tiles:</strong> ${wallBoxes} boxes ${wallPrice > 0 ? '(₹' + wallPrice.toFixed(2) + ')' : ''}</p>
        <hr>
        <p style="font-size:1.25rem;"><strong>Total Boxes: ${totalBoxes}</strong></p>
        <p style="font-size:1.25rem;"><strong>Total Price: ${totalPrice > 0 ? '₹' + totalPrice.toFixed(2) : 'Price TBD'}</strong></p>
    `;

    const summaryContainer = document.getElementById('bill-summary-content');
    if (summaryContainer) {
        summaryContainer.innerHTML = summaryHtml;
    }
}

// Initialize bill display on page load
document.addEventListener('DOMContentLoaded', function() {
    updateBillDisplay();
});
