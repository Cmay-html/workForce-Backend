#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Load local .env for dev runs (has no effect on Render unless file is present and allowed)
ENV_PATH = os.path.join(os.path.dirname(__file__), 'src', '.env')
load_dotenv(dotenv_path=ENV_PATH, override=False)

# Check for DB URL in common vars
db_url = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI')
if not db_url:
    print("DATABASE_URL/SQLALCHEMY_DATABASE_URI not set. Skipping database operations.")
    exit(0)

from src.app import create_app
from src.config import ProdConfig
from src.extensions import db
from flask_migrate import upgrade, stamp

app = create_app(ProdConfig)

with app.app_context():
    # Create all tables first (safe for existing tables)
    db.create_all()
    print("Tables created/verified")

    # Run migrations to add any missing columns
    try:
        upgrade()
        print("Database migration completed successfully")
    except Exception as e:
        print(f"Migration failed: {e}")
        # If migration fails, try to stamp the current version
        try:
            stamp()
            print("Database stamped to current version")
        except Exception as stamp_error:
            print(f"Stamping also failed: {stamp_error}")