import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    """Base configuration class for Learnova."""
    # --- Security ---
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-placeholder')

    # --- Database (PostgreSQL) ---
    # Docker uses 'db' as hostname, Local uses 'localhost'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- Redis Cache ---
    # Docker uses 'redis' as hostname
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # --- Gemini & AI Configuration ---
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    OPEN_AI_API_KEY = os.getenv('OPEN_AI_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = os.getenv('GROQ_MODEL')
    
    # --- Learnova Curriculum Constraints (2026 Rules) ---
    MIN_PROJECTS_PER_COURSE = 5
    MIN_SESSIONS_PER_PROJECT = 5

    # --- Flask-Mail (Email Service) ---
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() in ('true', '1')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() in ('true', '1')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER') or ('Learnova', 'noreply@learnova.com')
    MAIL_ADMIN_ADDRESS = os.getenv('MAIL_ADMIN_ADDRESS')

    # --- File Upload Configuration ---
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    # Folders inside app/static/uploads
    PROFILE_IMAGE_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads', 'profile_images')
    PDF_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads', 'pdfs')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit

    # --- URL & Threading Fixes ---
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'https'

    # --- Flask-Executor (Background AI/Email Tasks) ---
    EXECUTOR_TYPE = 'thread' 
    EXECUTOR_MAX_WORKERS = 10 
    EXECUTOR_PROPAGATE_EXCEPTIONS = True

    @staticmethod
    def init_app(app):
        """Initialize directories on app startup."""
        for folder in [Config.PROFILE_IMAGE_FOLDER, Config.PDF_FOLDER]:
            os.makedirs(folder, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True
    # If running locally without Docker, DATABASE_URL usually points to localhost
    # If running in Docker, the .env overrides this to point to 'db'

class ProductionConfig(Config):
    DEBUG = False
    MAIL_USE_TLS = True
    # For production, set these via environment variables on your host (Render/AWS)
    # SERVER_NAME = 'learnova.com' 

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}