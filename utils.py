from flask import request, jsonify
from flask_sqlalchemy import Pagination  # Import Pagination type hint
from flask_mail import Mail, Message
from flask import current_app
from werkzeug.utils import secure_filename
import os

# Pagination utility
def paginate_query(pagination, schema):
    items = schema.dump(pagination.items)
    return {
        'items': items,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': pagination.page,
        'per_page': pagination.per_page
    }

# Email utility (requires Flask-Mail configuration)
def send_email(to, subject, body):
    mail = Mail(current_app)
    msg = Message(subject, recipients=[to], body=body)
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

# File upload utility
def upload_file(file, folder='uploads'):
    if file and file.filename:
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, folder)
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        return os.path.join(folder, filename)
    return None