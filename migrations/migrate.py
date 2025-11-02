from run import app 
from flask_migrate import upgrade

with app.app_context():
    upgrade()

print("Alembic upgrade complete.")
