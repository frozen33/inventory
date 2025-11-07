import os
from datetime import timedelta

class Config:
    """Base configuration class"""

    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inventory.db')

    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Remember me for 7 days
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Flask-Login configuration
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = False  # Set to True in production
    REMEMBER_COOKIE_HTTPONLY = True

    # Application settings
    DEBUG = True  # Set to False in production
    TESTING = False

    # Image optimization settings
    IMAGE_QUALITY = 85  # JPEG quality (1-100)
    MAX_IMAGE_WIDTH = 1200
    MAX_IMAGE_HEIGHT = 1200
    THUMBNAIL_SIZE = (300, 300)

    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create upload directory if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

        # Create products subdirectory
        products_dir = os.path.join(Config.UPLOAD_FOLDER, 'products')
        os.makedirs(products_dir, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    DATABASE_PATH = ':memory:'  # Use in-memory database for testing

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}