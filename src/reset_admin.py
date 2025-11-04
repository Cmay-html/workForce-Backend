# reset_admin.py
from src.app import create_app
from src.models import User, db
from werkzeug.security import generate_password_hash

# Create the app and set up the context
app = create_app()
with app.app_context():
    # Check for existing admin
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(email='admin@example.com', role='admin')
        db.session.add(admin)
    admin.set_password('newadminpass123')  # Set a new password
    db.session.commit()