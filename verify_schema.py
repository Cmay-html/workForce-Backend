#!/usr/bin/env python3
"""
Verify database schema has all required columns.
This script checks if the users table has the verification_token and token_expires_at columns.
"""

import os
from dotenv import load_dotenv

# Load environment variables
ENV_PATH = os.path.join(os.path.dirname(__file__), 'src', '.env')
load_dotenv(dotenv_path=ENV_PATH, override=False)

from src.app import create_app
from src.config import ProdConfig
from src.extensions import db
from sqlalchemy import text

app = create_app(ProdConfig)

with app.app_context():
    try:
        # Check if verification_token column exists
        result = db.session.execute(text(
            """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='users' 
            AND column_name IN ('verification_token', 'token_expires_at')
            ORDER BY column_name;
            """
        ))
        
        columns = result.fetchall()
        
        print("=" * 60)
        print("DATABASE SCHEMA VERIFICATION")
        print("=" * 60)
        
        if len(columns) == 2:
            print("✓ SUCCESS: All required columns exist in users table")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
        else:
            print("✗ ERROR: Missing columns in users table")
            print(f"  Found {len(columns)} columns, expected 2")
            if columns:
                print("  Existing columns:")
                for col in columns:
                    print(f"    - {col[0]}: {col[1]}")
            
            missing = []
            found_cols = [col[0] for col in columns]
            if 'verification_token' not in found_cols:
                missing.append('verification_token')
            if 'token_expires_at' not in found_cols:
                missing.append('token_expires_at')
            
            if missing:
                print(f"  Missing columns: {', '.join(missing)}")
        
        print("=" * 60)
        
        # Also check all users table columns
        all_cols = db.session.execute(text(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name='users'
            ORDER BY ordinal_position;
            """
        ))
        
        print("\nAll columns in users table:")
        for col in all_cols:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            print(f"  - {col[0]}: {col[1]} ({nullable})")
        
    except Exception as e:
        print(f"Error checking schema: {e}")
        import traceback
        traceback.print_exc()

