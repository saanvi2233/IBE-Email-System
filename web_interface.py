"""
Web Interface for IBE Email System Demo
Flask application providing a user-friendly interface to demonstrate IBE functionality
"""
from flask import Flask, render_template, request, jsonify, session
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ibe.crypto_iface import DemoIBE, b64, ub64, canonicalize_identity
from pkg.auth_otp import request_otp, verify_otp
import secrets
import json

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Initialize IBE system (in production, load from persistent storage)
demo = DemoIBE()
MPK, MSK = demo.setup()

# Store for extracted keys (in-memory for demo)
extracted_keys = {}

@app.route('/')
def index():
    """Main demo interface"""
    return render_template('index.html')

@app.route('/api/system_info', methods=['GET'])
def system_info():
    """Get PKG system information"""
    return jsonify({
        'mpk': MPK,
        'msk_hidden': '***PROTECTED***',
        'algorithm': 'X25519 + ChaCha20-Poly1305',
        'status': 'operational'
    })

@app.route('/api/request_otp', methods=['POST'])
def api_request_otp():
    """Request OTP for private key extraction"""
    data = request.get_json()
    identity = canonicalize_identity(data.get('identity', ''))
    
    if not identity:
        return jsonify({'error': 'Identity required'}), 400
    
    # Generate and send OTP
    success = request_otp(identity)
    
    if success:
        return jsonify({
            'status': 'otp_sent',
            'identity': identity,
            'message': f'OTP sent to {identity}. Check SMTP debug server console.'
        }), 202
    else:
        return jsonify({'error': 'Failed to send OTP'}), 500

@app.route('/api/extract_key', methods=['POST'])
def api_extract_key():
    """Extract private key with OTP verification"""
    data = request.get_json()
    identity = canonicalize_identity(data.get('identity', ''))
    otp = data.get('otp', '')
    
    if not identity or not otp:
        return jsonify({'error': 'Identity and OTP required'}), 400
    
    # Verify OTP
    if not verify_otp(identity, otp):
        return jsonify({'error': 'Invalid or expired OTP'}), 403
    
    # Extract private key
    private_key = demo.extract(MSK, identity)
    private_key_b64 = b64(private_key)
    
    # Store in session (in production, use secure storage)
    extracted_keys[identity] = private_key_b64
    
    return jsonify({
        'status': 'success',
        'identity': identity,
        'private_key': private_key_b64,
        'message': f'Private key extracted successfully for {identity}'
    })

@app.route('/api/encrypt', methods=['POST'])
def api_encrypt():
    """Encrypt a message for an identity"""
    data = request.get_json()
    recipient = canonicalize_identity(data.get('recipient', ''))
    message = data.get('message', '')
    
    if not recipient or not message:
        return jsonify({'error': 'Recipient and message required'}), 400
    
    try:
        # Encrypt message
        envelope = demo.encrypt(recipient, message.encode('utf-8'))
        
        # Get ciphertext stats
        ciphertext_bytes = ub64(envelope['ciphertext'])
        
        return jsonify({
            'status': 'success',
            'recipient': recipient,
            'original_message': message,
            'envelope': envelope,
            'stats': {
                'message_length': len(message),
                'ciphertext_length': len(ciphertext_bytes),
                'overhead': len(ciphertext_bytes) - len(message.encode('utf-8')),
                'ephemeral_pub_length': 32,
                'nonce_length': 12,
                'mac_tag_length': 16
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/decrypt', methods=['POST'])
def api_decrypt():
    """Decrypt a message using private key"""
    data = request.get_json()
    identity = canonicalize_identity(data.get('identity', ''))
    envelope = data.get('envelope')
    
    if not identity or not envelope:
        return jsonify({'error': 'Identity and envelope required'}), 400
    
    # Check if we have the private key
    if identity not in extracted_keys:
        return jsonify({'error': 'Private key not found. Please extract key first.'}), 403
    
    try:
        # Get private key
        private_key = ub64(extracted_keys[identity])
        
        # Decrypt
        plaintext = demo.decrypt(private_key, envelope)
        decrypted_message = plaintext.decode('utf-8')
        
        return jsonify({
            'status': 'success',
            'identity': identity,
            'decrypted_message': decrypted_message
        })
    except Exception as e:
        return jsonify({'error': f'Decryption failed: {str(e)}'}), 500

@app.route('/api/demo_flow', methods=['POST'])
def api_demo_flow():
    """Complete demo flow for presentation"""
    data = request.get_json()
    recipient = canonicalize_identity(data.get('recipient', ''))
    message = data.get('message', '')
    otp = data.get('otp', '')
    
    if not recipient or not message or not otp:
        return jsonify({'error': 'Recipient, message, and OTP required'}), 400
    
    try:
        # Step 1: Verify OTP and extract key
        if not verify_otp(recipient, otp):
            return jsonify({'error': 'Invalid or expired OTP'}), 403
        
        private_key = demo.extract(MSK, recipient)
        extracted_keys[recipient] = b64(private_key)
        
        # Step 2: Encrypt
        envelope = demo.encrypt(recipient, message.encode('utf-8'))
        
        # Step 3: Decrypt
        plaintext = demo.decrypt(private_key, envelope)
        decrypted_message = plaintext.decode('utf-8')
        
        # Step 4: Verify
        match = (message == decrypted_message)
        
        return jsonify({
            'status': 'success',
            'steps': {
                '1_extract': f'Private key extracted for {recipient}',
                '2_encrypt': 'Message encrypted successfully',
                '3_decrypt': 'Message decrypted successfully',
                '4_verify': 'Messages match!' if match else 'Messages DO NOT match!'
            },
            'data': {
                'original_message': message,
                'decrypted_message': decrypted_message,
                'envelope': envelope,
                'match': match
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("="*70)
    print("IBE Email System - Web Interface")
    print("="*70)
    print()
    print("Starting web server on http://127.0.0.1:5001")
    print()
    print("IMPORTANT: Make sure SMTP debug server is running:")
    print("  python scripts/debug_smtp_server.py --port 1025")
    print()
    print("Open http://127.0.0.1:5001 in your browser to see the demo")
    print("="*70)
    print()
    
    app.run(debug=True, port=5001, host='127.0.0.1')
