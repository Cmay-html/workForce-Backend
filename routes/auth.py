from flask import app, request, jsonify
from flask_restx import Namespace, Resource, fields
from extensions import db
from models import User  
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from config import SECRET_KEY, JWT_ACCESS_EXPIRES, JWT_REFRESH_EXPIRES
from middlewares.auth_middleware import login_required, role_required
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter
from flask_cors import CORS

# Setup CORS

CORS(app)