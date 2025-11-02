from authlib.integrations.flask_client import OAuth
from flask import current_app, url_for
import requests

oauth = OAuth()

def init_google_oauth(app):
    """Initialize Google OAuth"""
    oauth.init_app(app)

    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

def get_google_auth_url(role='freelancer'):
    """Get Google OAuth authorization URL"""
    redirect_uri = url_for('google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri, state=role)

def get_google_user_info(token):
    """Get user info from Google using access token"""
    resp = oauth.google.get('https://openidconnect.googleapis.com/v1/userinfo', token=token)
    return resp.json() if resp else None