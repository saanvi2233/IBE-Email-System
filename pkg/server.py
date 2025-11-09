"""Tiny demo PKG server (Flask).

Endpoints:
- GET /mpk -> returns MPK JSON
- GET /get_pubkey?identity=... -> returns public key for identity (base64)
- POST /request_extract_code -> body: {"identity": "alice@example.com"}
    sends OTP to email; returns 202 Accepted
- POST /extract -> body: {"identity": "alice@example.com", "otp": "123456"}
    verifies OTP and returns private_key (base64) on success

For demo purposes this uses the DemoIBE implementation in `ibe/crypto_iface.py`.
Email OTP authentication is provided by `pkg/auth_otp.py`.
"""
from __future__ import annotations
import os
import json
from flask import Flask, request, jsonify

from ibe.crypto_iface import DemoIBE, b64, canonicalize_identity
from pkg.auth_otp import request_otp, verify_otp
import os
# Optionally use charm-crypto backend if requested
use_charm = os.environ.get('USE_CHARM') in ('1', 'true', 'yes')
CharmBackend = None
if use_charm:
    try:
        from ibe.charm_stub import CharmIBE, charm_available
        if charm_available():
            CharmBackend = CharmIBE
        else:
            print('USE_CHARM requested but charm is not available; falling back to DemoIBE')
    except Exception as _:
        print('Failed to import charm backend; falling back to DemoIBE:', _)

app = Flask(__name__)
if CharmBackend:
    try:
        pkg = CharmBackend()
        MPK, MSK = pkg.setup()
        print('Using charm-crypto IBE backend')
    except Exception as e:
        print('Charm backend initialization failed, falling back to DemoIBE:', e)
        pkg = DemoIBE()
        MSK = os.urandom(32)
        MPK, _ = pkg.setup()
else:
    pkg = DemoIBE()
    # In a real deploy store MSK in a secure HSM; for demo we keep MSK in memory
    MSK = os.urandom(32)
    MPK, _ = pkg.setup()


@app.route('/mpk', methods=['GET'])
def get_mpk():
    return jsonify(MPK)


@app.route('/get_pubkey', methods=['GET'])
def get_pubkey():
    identity = canonicalize_identity(request.args.get('identity', ''))
    if not identity:
        return jsonify({"error": "missing identity"}), 400
    pub = pkg.get_pubkey_for_identity(identity)
    if pub is None:
        return jsonify({"error": "unknown identity"}), 404
    return jsonify({"identity": identity, "pub_b64": b64(pub)})


@app.route('/request_extract_code', methods=['POST'])
def request_extract_code():
    """Request an OTP to be emailed to the identity (email address)."""
    data = request.get_json(force=True)
    identity = canonicalize_identity(data.get('identity', ''))
    if not identity or '@' not in identity:
        return jsonify({"error": "invalid identity"}), 400
    # TODO: add rate limiting per identity and per IP
    success = request_otp(identity)
    if not success:
        return jsonify({"error": "failed to send OTP"}), 500
    return jsonify({"status": "otp_sent", "identity": identity}), 202


@app.route('/extract', methods=['POST'])
def extract():
    """Verify OTP and issue private key for the identity."""
    data = request.get_json(force=True)
    identity = canonicalize_identity(data.get('identity', ''))
    otp = data.get('otp', '')
    if not identity:
        return jsonify({"error": "missing identity"}), 400
    if not otp:
        return jsonify({"error": "missing otp"}), 400
    # Verify OTP
    error = verify_otp(identity, otp)
    if error:
        return jsonify({"error": error}), 401
    # OTP verified; issue private key
    priv = pkg.extract(MSK, identity)
    return jsonify({"identity": identity, "private_b64": b64(priv)})


if __name__ == '__main__':
    port = int(os.environ.get('PKG_PORT', '5000'))
    print('Starting demo PKG on http://127.0.0.1:%d' % port)
    app.run(port=port, debug=True)
