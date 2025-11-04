#!/usr/bin/env python3
"""
Test script to verify auth endpoints return proper response format.
This tests that the response includes user data for frontend routing.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
ENV_PATH = os.path.join(os.path.dirname(__file__), 'src', '.env')
load_dotenv(dotenv_path=ENV_PATH, override=False)

from src.app import create_app
from src.config import DevConfig
from src.extensions import db
from src.models import User, ClientProfile
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

app = create_app(DevConfig)

def test_auth_response_format():
    """Test that auth endpoints return the expected response format."""
    with app.app_context():
        # Clean up test user if exists
        test_email = "test_response@example.com"
        existing_user = User.query.filter_by(email=test_email).first()
        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()
        
        print("=" * 60)
        print("TESTING AUTH RESPONSE FORMAT")
        print("=" * 60)
        
        # Test client registration
        with app.test_client() as client:
            print("\n1. Testing Client Registration...")
            response = client.post('/api/auth/register/client', json={
                'email': test_email,
                'password': 'testpass123',
                'company_name': 'Test Company'
            })
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 201:
                data = response.get_json()
                print("   ✓ Registration successful")
                
                # Check response structure
                assert 'access_token' in data, "Missing access_token"
                assert 'refresh_token' in data, "Missing refresh_token"
                assert 'user' in data, "Missing user data"
                print("   ✓ Response has all required fields")
                
                # Check user data structure
                user_data = data['user']
                assert 'id' in user_data, "Missing user.id"
                assert 'email' in user_data, "Missing user.email"
                assert 'role' in user_data, "Missing user.role"
                assert user_data['role'] == 'client', f"Expected role 'client', got '{user_data['role']}'"
                print("   ✓ User data has correct structure")
                print(f"   User: {user_data}")
                
            else:
                print(f"   ✗ Registration failed: {response.get_json()}")
                return False
            
            print("\n2. Testing Login...")
            response = client.post('/api/auth/login', json={
                'email': test_email,
                'password': 'testpass123'
            })
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print("   ✓ Login successful")
                
                # Check response structure
                assert 'access_token' in data, "Missing access_token"
                assert 'refresh_token' in data, "Missing refresh_token"
                assert 'user' in data, "Missing user data"
                print("   ✓ Response has all required fields")
                
                # Check user data structure
                user_data = data['user']
                assert 'id' in user_data, "Missing user.id"
                assert 'email' in user_data, "Missing user.email"
                assert 'role' in user_data, "Missing user.role"
                assert user_data['role'] == 'client', f"Expected role 'client', got '{user_data['role']}'"
                print("   ✓ User data has correct structure")
                print(f"   User: {user_data}")
                
            else:
                print(f"   ✗ Login failed: {response.get_json()}")
                return False
        
        # Clean up
        user = User.query.filter_by(email=test_email).first()
        if user:
            db.session.delete(user)
            db.session.commit()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nFrontend can now use the 'user' object to redirect:")
        print("  - if (user.role === 'client') navigate('/client/dashboard')")
        print("  - if (user.role === 'freelancer') navigate('/freelancer/dashboard')")
        print("=" * 60)
        
        return True

if __name__ == '__main__':
    try:
        success = test_auth_response_format()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

