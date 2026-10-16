import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app, url_for
from app.extensions import executor

from .templates import (
    PASSWORD_RESET_SUCCESS_HTML_BODY, 
    WELCOME_HTML_BODY, 
    LOGIN_ALERT_HTML_BODY, 
    PASSWORD_RESET_VERIFICATION_HTML_BODY,
    ACCOUNT_DELETED_HTML_BODY,
    SUPPORT_ASSURANCE_HTML_BODY,
    COURSE_FETCHED_HTML_BODY
)

logger = logging.getLogger(__name__)


def _send_sync_email(to_email: str, subject: str, html_body: str, text_body: str = None, reply_to: str = None) -> bool:
    """Synchronous worker that connects to Titan Mail via SMTP_SSL (port 465)."""
    app = current_app._get_current_object()
    mail_server = app.config.get('MAIL_SERVER', 'smtp.titan.email')
    mail_port = app.config.get('MAIL_PORT', 465)
    username = app.config.get('MAIL_USERNAME')
    password = app.config.get('MAIL_PASSWORD')
    mail_from = app.config.get('MAIL_FROM') or username
    from_name = app.config.get('MAIL_FROM_NAME', 'Learnova')

    if not username or not password:
        logger.warning("Titan Mail credentials missing in configuration. Email skipped.")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{from_name} <{mail_from}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to

    # Attach text fallback first (if available), then HTML body
    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(mail_server, mail_port, timeout=12) as server:
            server.login(username, password)
            server.sendmail(mail_from, [to_email], msg.as_string())
        logger.info(f"Email successfully delivered to {to_email} via Titan Mail.")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email} via Titan Mail: {e}")
        return False


def _get_external_url(endpoint: str, fallback_path: str = "/") -> str:
    """Safely build external URLs inside background executor threads."""
    app = current_app._get_current_object()
    base_url = app.config.get('FRONTEND_BASE_URL', 'http://127.0.0.1:5001')
    try:
        return url_for(endpoint, _external=True)
    except RuntimeError:
        return f"{base_url}{fallback_path}"


# =========================================================================
# 1. WELCOME NOTIFICATION
# =========================================================================
@executor.job
def send_welcome_email(recipient_email: str, username: str):
    """Sends a welcome email to the newly registered user."""
    dashboard_link = _get_external_url('main.get_user_profile', '/profile')
    subject = "Welcome to Learnova! 🚀"

    html_body = WELCOME_HTML_BODY.format(
        username=username, 
        dashboard_url=dashboard_link
    )
    text_body = f"Hi {username}, welcome to Learnova! Visit your dashboard here: {dashboard_link}"

    _send_sync_email(recipient_email, subject, html_body, text_body)


# =========================================================================
# 2. LOGIN SECURITY ALERT
# =========================================================================
@executor.job
def send_login_alert(recipient_email: str, username: str):
    """Sends a security alert when a successful login occurs."""
    reset_url = _get_external_url('auth.forgot_password', '/forgot-password')
    timestamp_str = datetime.now().strftime('%b %d, %Y at %I:%M %p')
    subject = "Security Alert: New Login Detected 🛡️"

    try:
        html_body = LOGIN_ALERT_HTML_BODY.format(
            username=username, 
            email=recipient_email,
            time=timestamp_str,
            reset_url=reset_url
        )
        text_body = (
            f"Hello {username}, a new login was detected on your account at {timestamp_str}. "
            f"If this wasn't you, reset your password here: {reset_url}"
        )
        _send_sync_email(recipient_email, subject, html_body, text_body)
    except Exception as e:
        logger.error(f"Failed to prepare login alert for {recipient_email}: {e}")


# =========================================================================
# 3. OTP VERIFICATION CODE
# =========================================================================
@executor.job
def send_password_reset_code(recipient_email: str, username: str, code: str):
    """Sends a 6-digit OTP code for password recovery."""
    subject = f"{code} is your Learnova verification code"
    text_body = f"Hi {username}, your Learnova password reset code is: {code}. This code expires in 10 minutes."

    try:
        html_body = PASSWORD_RESET_VERIFICATION_HTML_BODY.format(
            username=username, 
            code=code
        )
        _send_sync_email(recipient_email, subject, html_body, text_body)
    except Exception as e:
        logger.error(f"Failed to send OTP to {recipient_email}: {e}")


# =========================================================================
# 4. PASSWORD RESET CONFIRMATION
# =========================================================================
@executor.job
def send_password_reset_success_email(recipient_email: str, username: str):
    """Sends a confirmation email after a successful password reset."""
    subject = "Security Update: Password Reset Successful ✅"
    text_body = (
        f"Hi {username}, your Learnova password has been successfully reset. "
        f"If you did not perform this action, please contact our support team immediately."
    )

    try:
        html_body = PASSWORD_RESET_SUCCESS_HTML_BODY.format(username=username)
        _send_sync_email(recipient_email, subject, html_body, text_body)
    except Exception as e:
        logger.error(f"Failed to send reset success email to {recipient_email}: {e}")


# =========================================================================
# 5. ACCOUNT DELETION CONFIRMATION
# =========================================================================
@executor.job
def send_delete_account_success_email(recipient_email: str, username: str):
    """Sends a final confirmation email after an account is purged."""
    subject = "Confirmation: Your Learnova Account has been deleted"
    text_body = (
        f"Hello {username}, this email confirms that your Learnova account and all associated "
        f"data have been successfully deleted. We are sorry to see you go!"
    )

    try:
        html_body = ACCOUNT_DELETED_HTML_BODY.format(username=username)
        _send_sync_email(recipient_email, subject, html_body, text_body)
    except Exception as e:
        logger.error(f"Failed to send deletion email to {recipient_email}: {e}")


# =========================================================================
# 6. SUPPORT TICKET ASSURANCE & ADMIN NOTIFICATION
# =========================================================================
@executor.job
def send_support_assurance_email(recipient_email: str, username: str, issue_type: str, issue_details: str):
    """Sends confirmation to user and ticket notification to Admin with Reply-To."""
    app = current_app._get_current_object()
    admin_email = app.config.get('MAIL_ADMIN_ADDRESS')

    # 1. User confirmation
    user_subject = f"Learnova Support: Ticket Received ({issue_type})"
    user_text = (
        f"Hello {username},\n\nWe've received your report regarding '{issue_type}'. "
        f"Details: {issue_details}. Our team will get back to you soon."
    )
    try:
        user_html = SUPPORT_ASSURANCE_HTML_BODY.format(
            username=username, 
            issue_type=issue_type, 
            issue_details=issue_details
        )
        _send_sync_email(recipient_email, user_subject, user_html, user_text)

        # 2. Admin notification with Reply-To header pointing to user's email
        if admin_email:
            admin_subject = f"NEW TICKET [{issue_type}] from {username}"
            admin_text = f"""New Support Request:
-------------------
User: {username} ({recipient_email})
Type: {issue_type}

Message:
{issue_details}

--
End of Ticket.
"""
            admin_html = f"<pre style='font-family: monospace;'>{admin_text}</pre>"
            _send_sync_email(admin_email, admin_subject, admin_html, admin_text, reply_to=recipient_email)
            
    except Exception as e:
        logger.error(f"Failed to complete support email cycle for {recipient_email}: {e}")


# =========================================================================
# 7. CURRICULUM READY NOTIFICATION
# =========================================================================
@executor.job
def send_course_fetched_email(recipient_email: str, username: str, branch_name: str, course_grade: str, course_level: str, course_context: str):
    """Sends a notification when a requested course is ready."""
    courses_link = _get_external_url('main.get_user_profile', '/profile')
    subject = f"Your {course_context} - {course_grade} ({branch_name}) is Ready! 🚀"

    try:
        html_body = COURSE_FETCHED_HTML_BODY.format(
            username=username,
            level=course_level.capitalize(),
            context=course_context,
            grade=course_grade,
            branch=branch_name,
            dashboard_url=courses_link
        )
        text_body = (
            f"Hi {username}, the {course_context} {course_grade} {branch_name} course "
            f"you requested is now live on Learnova! View it here: {courses_link}"
        )
        _send_sync_email(recipient_email, subject, html_body, text_body)
    except Exception as e:
        logger.error(f"Failed to send course-fetched email to {recipient_email}: {e}")