import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class for Learnova."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-placeholder')

    # --- Database (PostgreSQL) ---
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- Redis Cache ---
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # --- AI Keys ---
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    OPEN_AI_API_KEY = os.getenv('OPEN_AI_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = os.getenv('GROQ_MODEL')
    
    # --- Curriculum Constraints ---
    MIN_PROJECTS_PER_COURSE = 5
    MIN_SESSIONS_PER_PROJECT = 5

    # --- Base URL for External Links ---
    FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'http://127.0.0.1:5001').rstrip('/')

    # --- Titan Mail SMTP Settings ---
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.titan.email')
    MAIL_PORT = int(os.getenv('MAIL_PORT') or 465)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_FROM = os.getenv('MAIL_FROM', os.getenv('MAIL_USERNAME'))
    MAIL_FROM_NAME = os.getenv('MAIL_FROM_NAME', 'Learnova')
    MAIL_ADMIN_ADDRESS = os.getenv('MAIL_ADMIN_ADDRESS')

    # --- File Upload Configuration ---
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PROFILE_IMAGE_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads', 'profile_images')
    PDF_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads', 'pdfs')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit

    # --- URL & Threading Fixes ---
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'https'

    # --- Flask-Executor Settings ---
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

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}