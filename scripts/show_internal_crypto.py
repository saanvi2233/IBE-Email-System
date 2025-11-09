"""
IBE Encryption/Decryption Internal Process Demonstration

This script shows exactly how the ciphertext is generated and decrypted internally.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ibe.crypto_iface import DemoIBE, b64, ub64
import json

print("="*70)
print("IBE INTERNAL ENCRYPTION/DECRYPTION DEMONSTRATION")
print("="*70)
print()

# Initialize IBE system
demo = DemoIBE()

# Setup phase
print("STEP 1: PKG SETUP")
print("-" * 70)
MPK, MSK = demo.setup()
print(f"Master Public Key (MPK):")
print(f"  Format: {type(MPK)}")
if isinstance(MPK, dict):
    for key, val in MPK.items():
        if isinstance(val, bytes):
            print(f"  {key}: {b64(val)}")
        else:
            print(f"  {key}: {val}")
else:
    print(f"  Base64: {b64(MPK)}")
    print(f"  Raw bytes (first 20): {MPK[:20].hex()}...")
print()
print(f"Master Secret Key (MSK) - KEPT SECRET BY PKG:")
print(f"  Base64: {b64(MSK)}")
print(f"  Raw bytes (first 20): {MSK[:20].hex()}...")
print(f"  Length: {len(MSK)} bytes")
print()

# Identity and message
identity = "sanvimps@gmail.com"
message = "Hello Sanvi, this is a secret message!"

print("STEP 2: SENDER ENCRYPTS MESSAGE")
print("-" * 70)
print(f"Recipient Identity: {identity}")
print(f"Original Message: '{message}'")
print(f"Message bytes: {message.encode('utf-8')}")
print(f"Message length: {len(message)} characters, {len(message.encode('utf-8'))} bytes")
print()

# Encryption
envelope = demo.encrypt(identity, message.encode('utf-8'))

print("ENCRYPTION PROCESS:")
print("  1. Generate random ephemeral private key (32 bytes)")
print("  2. Compute ephemeral public key using X25519")
print("  3. Derive shared secret from identity's public key + ephemeral private key")
print("  4. Use HKDF to derive encryption key from shared secret")
print("  5. Generate random nonce (12 bytes)")
print("  6. Encrypt message with ChaCha20-Poly1305 AEAD")
print()

print("CIPHERTEXT ENVELOPE (JSON):")
print("-" * 70)
print(json.dumps(envelope, indent=2))
print()

print("ENVELOPE COMPONENTS:")
print(f"  ephemeral_pub: {envelope['ephemeral_pub']}")
print(f"    - This is the sender's temporary public key (32 bytes)")
print(f"    - Used for ECDH key agreement")
print()
print(f"  nonce: {envelope['nonce']}")
print(f"    - Random 12-byte value for ChaCha20-Poly1305")
print(f"    - Ensures different ciphertext even for same message")
print()
print(f"  ciphertext: {envelope['ciphertext']}")
print(f"    - Encrypted message + authentication tag")
print(f"    - Length: {len(ub64(envelope['ciphertext']))} bytes")
print(f"    - Original message was {len(message.encode('utf-8'))} bytes")
print(f"    - Extra bytes are the 16-byte Poly1305 MAC tag")
print()

# Extract private key
print("STEP 3: RECIPIENT REQUESTS PRIVATE KEY FROM PKG")
print("-" * 70)
print(f"Identity: {identity}")
print("(In real system, recipient would authenticate with OTP first)")
print()

priv = demo.extract(MSK, identity)
print("PKG DERIVES PRIVATE KEY:")
print("  1. Takes Master Secret Key (MSK)")
print("  2. Takes recipient identity: 'sanvimps@gmail.com'")
print("  3. Derives private key using HKDF(MSK || identity)")
print()
print(f"Private Key:")
print(f"  Base64: {b64(priv)}")
print(f"  Raw bytes (first 20): {priv[:20].hex()}...")
print(f"  Length: {len(priv)} bytes")
print()

# Decryption
print("STEP 4: RECIPIENT DECRYPTS MESSAGE")
print("-" * 70)
plaintext = demo.decrypt(priv, envelope)

print("DECRYPTION PROCESS:")
print("  1. Extract ephemeral_pub from envelope")
print("  2. Compute shared secret using ECDH:")
print("     shared_secret = ECDH(private_key, ephemeral_pub)")
print("  3. Derive encryption key using HKDF(shared_secret)")
print("  4. Decrypt ciphertext using ChaCha20-Poly1305 with nonce")
print("  5. Verify authentication tag (ensures message wasn't tampered)")
print()

print(f"Decrypted Message: '{plaintext.decode('utf-8')}'")
print()

# Verification
print("STEP 5: VERIFICATION")
print("-" * 70)
if message == plaintext.decode('utf-8'):
    print("✓ SUCCESS! Decrypted message matches original message")
else:
    print("✗ FAILED! Messages don't match")
print()

print("="*70)
print("KEY INSIGHTS:")
print("="*70)
print()
print("1. CIPHERTEXT STRUCTURE:")
print("   - ephemeral_pub: Sender's temporary public key (32 bytes)")
print("   - nonce: Random value for encryption (12 bytes)")
print("   - ciphertext: Encrypted message + MAC tag")
print()
print("2. NO PRIOR KEY EXCHANGE:")
print("   - Sender encrypted using ONLY the recipient's email address")
print("   - No need to obtain recipient's public key beforehand!")
print()
print("3. AUTHENTICATED ENCRYPTION:")
print("   - ChaCha20-Poly1305 provides both confidentiality and integrity")
print("   - Any tampering with ciphertext will be detected during decryption")
print()
print("4. EPHEMERAL KEYS:")
print("   - Each encryption uses a fresh ephemeral keypair")
print("   - Same message encrypted twice produces different ciphertext")
print()
print("5. KEY DERIVATION:")
print("   - Private key is derived from MSK + identity")
print("   - Same identity always gets the same private key")
print("   - This is what makes it 'identity-based'!")
print()
print("="*70)
