import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()


class Config():
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    SECRET_KEY = os.getenv('SECRET_KEY')

class DevConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    DEBUG = True

class ProdConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False