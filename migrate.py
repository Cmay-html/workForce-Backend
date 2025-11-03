#!/usr/bin/env python3

from src.app import create_app
from src.config import ProdConfig
from src.extensions import db, migrate

app = create_app(ProdConfig)

with app.app_context():
    # Create all tables
    db.create_all()

    # Run migrations if needed
    try:
        migrate.upgrade()
        print("Database migration completed successfully")
    except Exception as e:
        print(f"Migration failed: {e}")
        # If migration fails, try to stamp the current version
        try:
            migrate.stamp()
            print("Database stamped to current version")
        except Exception as stamp_error:
            print(f"Stamping also failed: {stamp_error}")