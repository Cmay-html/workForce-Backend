from flask_mail import Message
from flask import current_app
import logging
import smtplib

logger = logging.getLogger(__name__)

class EmailService:
    # Email verification removed - using Google OAuth instead
    # send_verification_email method commented out

    @staticmethod
    def send_password_reset_email(email, reset_token):
        """Send password reset email to user"""
        try:
            subject = "Reset Your Password - WorkForce"
            reset_url = f"http://localhost:5000/auth/reset-password/{reset_token}"

            msg = Message(
                subject=subject,
                recipients=[email],
                body=f"""
                Password Reset Request

                You requested a password reset for your WorkForce account.

                Click the link below to reset your password:
                {reset_url}

                This link will expire in 1 hour.

                If you didn't request this reset, please ignore this email.

                Best regards,
                WorkForce Team
                """,
                html=f"""
                <h2>Password Reset Request</h2>

                <p>You requested a password reset for your WorkForce account.</p>

                <p>Click the link below to reset your password:</p>

                <a href="{reset_url}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0;">
                    Reset Password
                </a>

                <p>This link will expire in 1 hour.</p>

                <p>If you didn't request this reset, please ignore this email.</p>

                <p>Best regards,<br>WorkForce Team</p>
                """
            )

            current_app.extensions['mail'].send(msg)
            logger.info(f"Password reset email sent to {email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")
            return False