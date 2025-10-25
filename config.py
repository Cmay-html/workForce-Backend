import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')  # Added for Flask security
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')  # Changed to DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Moved to base Config

    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

   

class DevConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    DEBUG = True

class ProdConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    DEBUG = False

# Map environments to config classes
config = {
    'development': DevConfig,
    'production': ProdConfig
}