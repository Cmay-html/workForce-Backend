#!/usr/bin/env python3
"""
Fix script to create client_profile for user 16 on production database
This connects directly to the Render PostgreSQL database with SSL
"""
import psycopg2
import sys

# Production database - requires SSL
DATABASE_URL = "postgresql://workforcedb_user:eTjq4PKlUwrDNtYkrvWcNNSWDExZ4Hhj@dpg-d43pmaemcj7s73bc0go0-a.oregon-postgres.render.com/workforcedb?sslmode=require"

try:
    # Connect to database with SSL
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check if user 16 exists
    cur.execute("SELECT id, email, role, first_name, last_name FROM users WHERE id = 16")
    user = cur.fetchone()
    
    if not user:
        print("❌ User 16 not found")
        sys.exit(1)
    
    user_id, email, role, first_name, last_name = user
    print(f"✓ Found user: {email} (role: {role})")
    
    # Check if client_profile exists
    cur.execute("SELECT id FROM client_profiles WHERE user_id = 16")
    profile = cur.fetchone()
    
    if profile:
        print(f"✓ Client profile already exists with ID: {profile[0]}")
    else:
        # Create client profile
        company_name = f"{first_name or ''} {last_name or ''}".strip() or email.split("@")[0]
        
        cur.execute("""
            INSERT INTO client_profiles (user_id, company_name, phone_number, address)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (user_id, company_name, "", ""))
        
        new_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"✓ Created client profile with ID: {new_id}")
        print(f"✓ User {user_id} ({email}) can now create projects!")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
