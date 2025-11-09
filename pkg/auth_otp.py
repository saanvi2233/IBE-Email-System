"""Email-based OTP (one-time password) authentication for PKG /extract endpoint.

This module provides:
- OTP generation and storage (in-memory for demo; use Redis in production).
- Email sending via SMTP (supports debug SMTP server for local testing).
- Rate limiting and expiry logic.

Configuration via environment variables:
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM_EMAIL
- OTP_TTL_SECONDS (default 600 = 10 minutes)
- OTP_MAX_ATTEMPTS (default 3)
"""
from __future__ import annotations
import os
import secrets
import time
import hashlib
import hmac
from smtplib import SMTP
from email.message import EmailMessage
from typing import Optional

# Configuration from env
SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '1025'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL', 'noreply@ibe-pkg.local')
OTP_TTL_SECONDS = int(os.environ.get('OTP_TTL_SECONDS', '600'))
OTP_MAX_ATTEMPTS = int(os.environ.get('OTP_MAX_ATTEMPTS', '3'))

# In-memory OTP store: {identity: {otp_hash, salt, expiry, attempts}}
# Production: use Redis or a DB with TTL
otp_store = {}


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of the given length."""
    return '{:0{}d}'.format(secrets.randbelow(10**length), length)


def request_otp(identity: str) -> bool:
    """Generate and email an OTP for the given identity.
    
    Returns True if OTP was sent successfully, False otherwise.
    Stores hashed OTP in the otp_store with expiry.
    """
    otp = generate_otp(6)
    salt = secrets.token_bytes(16)
    otp_hash = hashlib.sha256(salt + otp.encode('utf8')).hexdigest()
    expiry = time.time() + OTP_TTL_SECONDS
    otp_store[identity] = {
        'otp_hash': otp_hash,
        'salt': salt.hex(),
        'expiry': expiry,
        'attempts': 0
    }
    # Send email
    try:
        send_otp_email(identity, otp)
        return True
    except Exception as e:
        print(f'Failed to send OTP email to {identity}: {e}')
        return False


def verify_otp(identity: str, otp: str) -> Optional[str]:
    """Verify the OTP for the given identity.
    
    Returns None on success, or an error string ('expired', 'invalid', 'too_many_attempts').
    """
    rec = otp_store.get(identity)
    if not rec:
        return 'no_otp_found'
    if time.time() > rec['expiry']:
        del otp_store[identity]
        return 'expired'
    if rec['attempts'] >= OTP_MAX_ATTEMPTS:
        return 'too_many_attempts'
    # Compare hash
    salt = bytes.fromhex(rec['salt'])
    computed = hashlib.sha256(salt + otp.encode('utf8')).hexdigest()
    if not hmac.compare_digest(computed, rec['otp_hash']):
        rec['attempts'] += 1
        return 'invalid'
    # Success: remove OTP after successful verification
    del otp_store[identity]
    return None


def send_otp_email(to_email: str, otp: str):
    """Send an OTP via email using configured SMTP server."""
    msg = EmailMessage()
    msg['Subject'] = 'Your IBE PKG verification code'
    msg['From'] = SMTP_FROM_EMAIL
    msg['To'] = to_email
    msg.set_content(
        f'Your verification code is: {otp}\n\n'
        f'This code expires in {OTP_TTL_SECONDS // 60} minutes.\n\n'
        f'If you did not request this code, please ignore this email.'
    )
    # For local dev with debugging SMTP server (no TLS/auth), handle gracefully
    try:
        with SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
            # Only call starttls if not using debug server on localhost
            if SMTP_PORT != 1025 and SMTP_HOST != 'localhost':
                s.starttls()
            if SMTP_USER and SMTP_PASS:
                s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    except Exception as e:
        # If running debug SMTP server, print OTP to console as fallback
        print(f'[DEBUG] OTP for {to_email}: {otp}')
        raise e
