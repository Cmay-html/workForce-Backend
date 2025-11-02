import os
import psycopg2
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')  # Added for Flask security
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Moved to base Config

    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

class DevConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql+psycopg2://postgres:postgres@localhost:5432/workdb')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'bd6f47d5fbe6130531225d993ce47f56')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your-email@gmail.com'
    MAIL_PASSWORD = 'your-app-password'

class ProdConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    DEBUG = False

# Map environments to config classes
config = {
    'development': DevConfig,
    'production': ProdConfig
}
