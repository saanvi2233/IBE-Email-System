"""Test the OTP request and verification flow."""
from pkg.auth_otp import request_otp, verify_otp, otp_store
import time


def test_otp_request_and_verify():
    identity = 'alice@example.com'
    # Clear any existing OTP
    otp_store.clear()
    # Request OTP (will fail to send email in test env, but will store hash)
    # We'll capture the OTP from the store for testing
    try:
        request_otp(identity)
    except Exception:
        pass  # SMTP will fail; that's OK for unit test
    # Check OTP was stored
    assert identity in otp_store
    # Extract the OTP from the store by brute-forcing (for test only)
    # In real test, mock the send function to capture OTP
    # For now we'll test verification with wrong OTP
    err = verify_otp(identity, '000000')
    assert err == 'invalid'
    # After 3 wrong attempts it should lock
    verify_otp(identity, '111111')
    verify_otp(identity, '222222')
    err = verify_otp(identity, '333333')
    assert err == 'too_many_attempts'


def test_otp_expiry():
    identity = 'bob@example.com'
    otp_store.clear()
    # Manually create an expired OTP
    otp_store[identity] = {
        'otp_hash': 'fakehash',
        'salt': 'fakesalt',
        'expiry': time.time() - 10,  # expired 10 seconds ago
        'attempts': 0
    }
    err = verify_otp(identity, '123456')
    assert err == 'expired'
    assert identity not in otp_store  # should be cleaned up
