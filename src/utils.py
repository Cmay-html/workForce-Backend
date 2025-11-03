import os
from flask import url_for
from flask_mail import Message
from extensions import mail
from urllib.parse import quote

def send_verification_email(user, base_url):
    """Send email verification link to user"""
    import logging

    try:
        token = user.generate_verification_token()
        verification_url = f"{base_url}/verify-email?token={token}&email={quote(user.email)}"

        msg = Message(
            subject='Verify Your Email - Workforce Platform',
            recipients=[user.email],
            html=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Welcome to Workforce Platform!</h2>
                <p>Please verify your email address to complete your registration.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}"
                       style="background-color: #007bff; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    This link will expire in 24 hours. If you didn't create an account, please ignore this email.
                </p>
                <p style="color: #666; font-size: 14px;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{verification_url}">{verification_url}</a>
                </p>
            </div>
            """
        )

        mail.send(msg)
        return True
    except Exception as e:
        logging.error(f"Error sending verification email to {user.email}: {str(e)}")
        return False

def send_password_reset_email(user, reset_token, base_url):
    """Send password reset email to user"""
    import logging

    try:
        reset_url = f"{base_url}/reset-password?token={reset_token}&email={quote(user.email)}"

        msg = Message(
            subject='Reset Your Password - Workforce Platform',
            recipients=[user.email],
            html=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Password Reset Request</h2>
                <p>You requested a password reset for your Workforce Platform account.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}"
                       style="background-color: #dc3545; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    This link will expire in 1 hour. If you didn't request a password reset, please ignore this email.
                </p>
                <p style="color: #666; font-size: 14px;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{reset_url}">{reset_url}</a>
                </p>
            </div>
            """
        )

        mail.send(msg)
        return True
    except Exception as e:
        logging.error(f"Error sending password reset email to {user.email}: {str(e)}")
        return False

# Pagination utility
def paginate_query(pagination, schema):
    """
    Takes a SQLAlchemy pagination object and a Marshmallow schema,
    and returns a serializable dictionary. Flask-RESTX handles the
    envelope wrapping.
    """
    items = schema.dump(pagination.items)
    return {
        'items': items,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': pagination.page,
        'per_page': pagination.per_page
    }