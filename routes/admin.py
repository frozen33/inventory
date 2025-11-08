"""
Admin Routes
User management and audit log viewing for administrators
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import login_required, current_user
from functools import wraps
from models.user import User
from models.product import Product
from models.product_audit_log import ProductAuditLog

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))

        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('inventory.dashboard'))

        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with system overview"""
    try:
        # Get statistics
        all_users = User.get_all_users(current_app.config['DATABASE_PATH'])
        total_users = len(all_users)
        admin_count = sum(1 for u in all_users if u['role'] == 'admin')

        total_products = Product.get_total_count(database_path=current_app.config['DATABASE_PATH'])

        activity_stats = ProductAuditLog.get_activity_stats(current_app.config['DATABASE_PATH'])

        # Get recent activity
        recent_activity = ProductAuditLog.get_recent_activity(
            limit=20,
            database_path=current_app.config['DATABASE_PATH']
        )

        return render_template('admin/dashboard.html',
                             total_users=total_users,
                             admin_count=admin_count,
                             total_products=total_products,
                             activity_stats=activity_stats,
                             recent_activity=recent_activity)

    except Exception as e:
        flash('Error loading admin dashboard.', 'error')
        print(f"Admin dashboard error: {e}")
        return render_template('admin/dashboard.html',
                             total_users=0,
                             admin_count=0,
                             total_products=0,
                             activity_stats={},
                             recent_activity=[])


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users with management options"""
    try:
        all_users = User.get_all_users(current_app.config['DATABASE_PATH'])

        return render_template('admin/users.html', users=all_users)

    except Exception as e:
        flash('Error loading users list.', 'error')
        print(f"Admin users error: {e}")
        return render_template('admin/users.html', users=[])


@admin_bp.route('/users/<int:user_id>/promote', methods=['POST'])
@login_required
@admin_required
def promote_user(user_id):
    """Promote user to admin"""
    try:
        if user_id == current_user.id:
            flash('You are already an admin.', 'info')
            return redirect(url_for('admin.users'))

        success = User.promote_to_admin(user_id, current_app.config['DATABASE_PATH'])

        if success:
            # Get user email for message
            user = User.get_by_id(user_id, current_app.config['DATABASE_PATH'])
            flash(f'User {user.email} promoted to admin successfully.', 'success')
        else:
            flash('Error promoting user. Please try again.', 'error')

    except Exception as e:
        flash('Error promoting user.', 'error')
        print(f"Promote user error: {e}")

    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/demote', methods=['POST'])
@login_required
@admin_required
def demote_user(user_id):
    """Demote admin to regular user"""
    try:
        if user_id == current_user.id:
            flash('You cannot demote yourself.', 'error')
            return redirect(url_for('admin.users'))

        success = User.demote_from_admin(user_id, current_app.config['DATABASE_PATH'])

        if success:
            # Get user email for message
            user = User.get_by_id(user_id, current_app.config['DATABASE_PATH'])
            flash(f'User {user.email} demoted to regular user.', 'success')
        else:
            flash('Cannot demote the last admin user.', 'error')

    except Exception as e:
        flash('Error demoting user.', 'error')
        print(f"Demote user error: {e}")

    return redirect(url_for('admin.users'))


@admin_bp.route('/audit-log')
@login_required
@admin_required
def audit_log():
    """View complete audit log with filtering"""
    try:
        # Get filter parameters
        action_filter = request.args.get('action', '')
        user_filter = request.args.get('user', '')
        limit = int(request.args.get('limit', 100))

        # Get all activity
        activity = ProductAuditLog.get_recent_activity(
            limit=limit,
            database_path=current_app.config['DATABASE_PATH']
        )

        # Apply filters (client-side for simplicity, could be moved to database query)
        if action_filter:
            activity = [a for a in activity if a['action'] == action_filter]

        if user_filter:
            try:
                user_id = int(user_filter)
                activity = [a for a in activity if a['user_id'] == user_id]
            except ValueError:
                pass

        # Get list of all users for filter dropdown
        all_users = User.get_all_users(current_app.config['DATABASE_PATH'])

        return render_template('admin/audit_log.html',
                             activity=activity,
                             all_users=all_users,
                             action_filter=action_filter,
                             user_filter=user_filter)

    except Exception as e:
        flash('Error loading audit log.', 'error')
        print(f"Audit log error: {e}")
        return render_template('admin/audit_log.html',
                             activity=[],
                             all_users=[],
                             action_filter='',
                             user_filter='')


@admin_bp.route('/audit-log/product/<int:product_id>')
@login_required
@admin_required
def product_history(product_id):
    """View history for a specific product"""
    try:
        # Get product info
        product = Product.get_by_id(product_id, current_app.config['DATABASE_PATH'])

        # Get product history
        history = ProductAuditLog.get_product_history(
            product_id=product_id,
            limit=100,
            database_path=current_app.config['DATABASE_PATH']
        )

        return render_template('admin/product_history.html',
                             product=product.to_dict(current_app.config['DATABASE_PATH']) if product else None,
                             history=history,
                             product_id=product_id)

    except Exception as e:
        flash('Error loading product history.', 'error')
        print(f"Product history error: {e}")
        return redirect(url_for('admin.audit_log'))


@admin_bp.route('/audit-log/user/<int:user_id>')
@login_required
@admin_required
def user_activity(user_id):
    """View activity for a specific user"""
    try:
        # Get user info
        user = User.get_by_id(user_id, current_app.config['DATABASE_PATH'])

        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin.users'))

        # Get user activity
        activity = ProductAuditLog.get_user_activity(
            user_id=user_id,
            limit=100,
            database_path=current_app.config['DATABASE_PATH']
        )

        return render_template('admin/user_activity.html',
                             user=user.to_dict(),
                             activity=activity)

    except Exception as e:
        flash('Error loading user activity.', 'error')
        print(f"User activity error: {e}")
        return redirect(url_for('admin.users'))


@admin_bp.route('/stats')
@login_required
@admin_required
def stats():
    """View detailed statistics (API endpoint)"""
    try:
        stats_data = ProductAuditLog.get_activity_stats(current_app.config['DATABASE_PATH'])

        return jsonify({
            'success': True,
            'stats': stats_data
        })

    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load statistics'
        }), 500
