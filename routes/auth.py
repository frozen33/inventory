from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models.user import User
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"

    if len(password) > 128:
        return False, "Password must be less than 128 characters"

    return True, "Password is valid"

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('inventory.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        # Validation
        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('auth/login.html', email=email)

        if not validate_email(email):
            flash('Please provide a valid email address.', 'error')
            return render_template('auth/login.html', email=email)

        # Try to find user
        try:
            user = User.get_by_email(email)

            if user and user.check_password(password):
                login_user(user, remember=remember)
                flash(f'Welcome back, {user.email}!', 'success')

                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('inventory.dashboard'))
            else:
                flash('Invalid email or password.', 'error')

        except Exception as e:
            flash('An error occurred during login. Please try again.', 'error')
            print(f"Login error: {e}")

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('inventory.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not email or not password or not confirm_password:
            flash('Please fill in all fields.', 'error')
            return render_template('auth/register.html', email=email)

        if not validate_email(email):
            flash('Please provide a valid email address.', 'error')
            return render_template('auth/register.html', email=email)

        is_valid, password_message = validate_password(password)
        if not is_valid:
            flash(password_message, 'error')
            return render_template('auth/register.html', email=email)

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html', email=email)

        # Check if user already exists
        try:
            if User.email_exists(email):
                flash('An account with this email already exists.', 'error')
                return render_template('auth/register.html', email=email)

            # Create new user
            user = User.create_user(email, password)

            if user:
                login_user(user)
                flash(f'Account created successfully! Welcome, {user.email}!', 'success')
                return redirect(url_for('inventory.dashboard'))
            else:
                flash('Failed to create account. Please try again.', 'error')

        except Exception as e:
            flash('An error occurred during registration. Please try again.', 'error')
            print(f"Registration error: {e}")

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    user_email = current_user.email
    logout_user()
    flash(f'You have been logged out successfully. Goodbye!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not current_password or not new_password or not confirm_password:
            flash('Please fill in all fields.', 'error')
            return render_template('auth/change_password.html')

        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html')

        is_valid, password_message = validate_password(new_password)
        if not is_valid:
            flash(password_message, 'error')
            return render_template('auth/change_password.html')

        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('auth/change_password.html')

        if current_password == new_password:
            flash('New password must be different from current password.', 'error')
            return render_template('auth/change_password.html')

        try:
            current_user.update_password(new_password)
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))

        except Exception as e:
            flash('Failed to change password. Please try again.', 'error')
            print(f"Password change error: {e}")

    return render_template('auth/change_password.html')