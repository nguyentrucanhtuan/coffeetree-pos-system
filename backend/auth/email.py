"""Email utilities — SMTP sender with console fallback for dev mode."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def _send_email(to_email: str, subject: str, html_body: str) -> None:
    """Send an email via SMTP. Falls back to console log if SMTP_HOST is empty."""
    if not settings.SMTP_HOST:
        # Dev mode — console log
        logger.info("=" * 60)
        logger.info("📧 EMAIL (dev mode — no SMTP configured)")
        logger.info("  To:      %s", to_email)
        logger.info("  Subject: %s", subject)
        logger.info("  Body:\n%s", html_body)
        logger.info("=" * 60)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        if settings.SMTP_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)

        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

        server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
        server.quit()
        logger.info("Email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        raise


def send_reset_email(to_email: str, reset_token: str) -> None:
    """Send a password reset email."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    html = f"""
    <h2>Reset mật khẩu — CoffeeTree</h2>
    <p>Bạn đã yêu cầu đặt lại mật khẩu. Click link sau để tiếp tục:</p>
    <p><a href="{reset_url}">{reset_url}</a></p>
    <p>Link có hiệu lực trong 1 giờ.</p>
    <p>Nếu bạn không yêu cầu, hãy bỏ qua email này.</p>
    """
    _send_email(to_email, "Reset mật khẩu — CoffeeTree", html)


def send_verify_email(to_email: str, verify_token: str) -> None:
    """Send an email verification link."""
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={verify_token}"
    html = f"""
    <h2>Xác minh email — CoffeeTree</h2>
    <p>Chào mừng bạn! Vui lòng xác minh email bằng link sau:</p>
    <p><a href="{verify_url}">{verify_url}</a></p>
    <p>Link có hiệu lực trong 24 giờ.</p>
    """
    _send_email(to_email, "Xác minh email — CoffeeTree", html)
