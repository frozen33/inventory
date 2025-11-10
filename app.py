import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user
from config import config
from database import init_db, check_database

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.get_by_id(int(user_id), app.config['DATABASE_PATH'])

    # Register blueprints
    from routes.auth import auth_bp
    from routes.inventory import inventory_bp
    from routes.admin import admin_bp
    from routes.calculator import calculator_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(admin_bp)  # Admin routes already have /admin prefix
    app.register_blueprint(calculator_bp)  # Calculator routes already have /calculator prefix

    # Main routes
    @app.route('/')
    def index():
        """Home page - redirect based on authentication"""
        if current_user.is_authenticated:
            return redirect(url_for('inventory.dashboard'))
        return redirect(url_for('auth.login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Main dashboard - redirect to inventory"""
        return redirect(url_for('inventory.dashboard'))

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    # Context processors
    @app.context_processor
    def inject_user():
        """Make current user available in all templates"""
        return dict(current_user=current_user)

    # Template filters
    @app.template_filter('datetime')
    def datetime_filter(value, format='%Y-%m-%d %H:%M'):
        """Format datetime for templates"""
        if value is None:
            return ""
        from datetime import datetime
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return value
        return value.strftime(format)

    @app.template_filter('currency')
    def currency_filter(value):
        """Format currency for templates"""
        if value is None:
            return "N/A"
        try:
            return f"₹{float(value):,.2f}"
        except:
            return str(value)

    return app

def initialize_database():
    """Initialize database if it doesn't exist"""
    database_path = 'inventory.db'

    if not os.path.exists(database_path):
        print("Database not found. Initializing...")
        init_db(database_path)

        # Create test data for development
        from database import create_test_data
        create_test_data(database_path)
        print("Database initialized with test data!")
    else:
        print("Database found. Checking structure...")
        check_database(database_path)

if __name__ == '__main__':
    # Initialize database
    initialize_database()

    # Get configuration from environment
    config_name = os.environ.get('FLASK_ENV', 'development')

    # Create app
    app = create_app(config_name)

    # Get host and port from environment or use defaults
    host = os.environ.get('HOST', '0.0.0.0')  # Listen on all interfaces
    port = int(os.environ.get('PORT', 5000))

    print(f"""
    🚀 Inventory Management System Starting...

    📊 Configuration: {config_name}
    🌐 Server: http://{host}:{port}
    📁 Database: {app.config['DATABASE_PATH']}
    📂 Uploads: {app.config['UPLOAD_FOLDER']}

    🔑 Test Login: test@example.com / testpass123
    """)

    # Run the application
    app.run(
        host=host,
        port=port,
        debug=app.config['DEBUG']
    )