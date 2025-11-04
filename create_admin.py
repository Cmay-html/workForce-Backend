"""
Script to create an admin user directly in the database
"""
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

# Load environment variables
load_dotenv('src/.env')

# Import app and models
from src.app import create_app
from src.extensions import db
from src.models import User
from src.config import ProdConfig

def create_admin():
    """Create admin user in the database"""
    app = create_app(config=ProdConfig)
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@test.com').first()
        
        if existing_admin:
            print(f"Admin user already exists with email: admin@test.com")
            print(f"User ID: {existing_admin.id}")
            print(f"Role: {existing_admin.role}")
            return
        
        # Create new admin user
        admin = User(
            email='admin@test.com',
            password_hash=generate_password_hash('adminpass'),
            role='admin',
            is_verified=True,
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("✓ Admin user created successfully!")
        print(f"Email: {admin.email}")
        print(f"Password: adminpass")
        print(f"Role: {admin.role}")
        print(f"User ID: {admin.id}")

if __name__ == '__main__':
    create_admin()
