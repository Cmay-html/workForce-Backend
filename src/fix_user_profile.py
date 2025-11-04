#!/usr/bin/env python3
"""
Fix script to create client_profile for user 16
Run this from the workForce-Backend directory: python src/fix_user_profile.py
"""
import os
import sys

# Set working directory to src
src_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(src_dir)

# Import directly from app which handles the imports correctly
from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Check if user 16 exists and get their info
    result = db.session.execute(text("""
        SELECT id, email, role, first_name, last_name 
        FROM users 
        WHERE id = 16
    """)).fetchone()
    
    if not result:
        print("User 16 not found")
        sys.exit(1)
    
    user_id, email, role, first_name, last_name = result
    print(f"Found user: {email} (role: {role})")
    
    # Check if client_profile exists
    profile_check = db.session.execute(text("""
        SELECT id FROM client_profiles WHERE user_id = 16
    """)).fetchone()
    
    if profile_check:
        print(f"Client profile already exists with ID: {profile_check[0]}")
    else:
        # Create client profile
        company_name = f"{first_name} {last_name}" if first_name and last_name else email.split("@")[0]
        
        db.session.execute(text("""
            INSERT INTO client_profiles (user_id, company_name, phone_number, address)
            VALUES (:user_id, :company_name, '', '')
        """), {"user_id": user_id, "company_name": company_name})
        
        db.session.commit()
        
        # Get the new profile ID
        new_profile = db.session.execute(text("""
            SELECT id FROM client_profiles WHERE user_id = 16
        """)).fetchone()
        
        print(f"✓ Created client profile with ID: {new_profile[0]}")
        print(f"User {user_id} can now create projects")
