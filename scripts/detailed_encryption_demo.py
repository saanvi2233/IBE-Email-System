"""
Detailed Encryption/Decryption Breakdown for: "World is here"

This shows EXACTLY what happens internally when encrypting and decrypting.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ibe.crypto_iface import DemoIBE, b64, ub64
import json

print("="*80)
print(" DETAILED IBE ENCRYPTION BREAKDOWN: 'World is here' ")
print("="*80)
print()

# Setup
demo = DemoIBE()
MPK, MSK = demo.setup()

identity = "sanvimps@gmail.com"
message = "World is here"

print("📝 ORIGINAL MESSAGE")
print("-" * 80)
print(f"Message: '{message}'")
print(f"Message as bytes: {message.encode('utf-8')}")
print(f"Hex representation: {message.encode('utf-8').hex()}")
print(f"Length: {len(message)} characters = {len(message.encode('utf-8'))} bytes")
print()

print("🔐 ENCRYPTION STEP-BY-STEP")
print("-" * 80)
print()

# Encrypt
envelope = demo.encrypt(identity, message.encode('utf-8'))

print("Step 1: Generate Ephemeral Keypair")
print("  - Generate random 32-byte private key")
print("  - Compute X25519 public key from private key")
print(f"  - Ephemeral Public Key: {envelope['ephemeral_pub']}")
ephemeral_pub_bytes = ub64(envelope['ephemeral_pub'])
print(f"  - Length: {len(ephemeral_pub_bytes)} bytes")
print(f"  - Hex: {ephemeral_pub_bytes.hex()}")
print()

print("Step 2: Derive Recipient's Public Key")
print(f"  - Identity: {identity}")
print("  - Canonicalize: sanvimps@gmail.com (already lowercase)")
print("  - Derive public key from identity using HKDF(MPK || identity)")
print()

print("Step 3: Perform ECDH (Elliptic Curve Diffie-Hellman)")
print("  - Combine ephemeral private key with recipient's public key")
print("  - Result: shared secret (32 bytes)")
print("  - This shared secret is known only to sender and recipient")
print()

print("Step 4: Derive Encryption Key")
print("  - Use HKDF to derive encryption key from shared secret")
print("  - HKDF-SHA256 produces a 32-byte key for ChaCha20-Poly1305")
print()

print("Step 5: Generate Random Nonce")
print(f"  - Nonce: {envelope['nonce']}")
nonce_bytes = ub64(envelope['nonce'])
print(f"  - Length: {len(nonce_bytes)} bytes")
print(f"  - Hex: {nonce_bytes.hex()}")
print("  - Purpose: Ensures same message encrypts differently each time")
print()

print("Step 6: Encrypt with ChaCha20-Poly1305 AEAD")
print("  - Input: 'World is here' (13 bytes)")
print("  - Algorithm: ChaCha20 stream cipher + Poly1305 MAC")
print("  - ChaCha20 XORs plaintext with keystream")
print("  - Poly1305 computes 16-byte authentication tag")
print()

ciphertext_bytes = ub64(envelope['ciphertext'])
print(f"  - Output Ciphertext: {envelope['ciphertext']}")
print(f"  - Length: {len(ciphertext_bytes)} bytes")
print(f"  - Breakdown:")
print(f"    • Encrypted message: {len(ciphertext_bytes) - 16} bytes")
print(f"    • Poly1305 MAC tag: 16 bytes")
print(f"  - Hex: {ciphertext_bytes.hex()}")
print()

print("="*80)
print(" COMPLETE ENCRYPTED ENVELOPE (JSON) ")
print("="*80)
print(json.dumps(envelope, indent=2))
print()

print("="*80)
print(" DECRYPTION STEP-BY-STEP ")
print("="*80)
print()

# Extract private key
priv = demo.extract(MSK, identity)

print("Step 1: Recipient Requests Private Key from PKG")
print(f"  - Identity: {identity}")
print("  - PKG derives: HKDF(MSK || 'sanvimps@gmail.com')")
print(f"  - Private Key: {b64(priv)}")
print(f"  - Length: {len(priv)} bytes")
print(f"  - Hex: {priv.hex()}")
print()

print("Step 2: Extract Ephemeral Public Key from Envelope")
print(f"  - Ephemeral Pub: {envelope['ephemeral_pub']}")
print("  - This is the sender's temporary public key")
print()

print("Step 3: Perform ECDH (Recipient's Side)")
print("  - Combine recipient's private key with ephemeral public key")
print("  - Result: SAME shared secret as sender computed!")
print("  - This is the magic of ECDH - both sides get same secret")
print()

print("Step 4: Derive Decryption Key")
print("  - Use HKDF on shared secret (same as encryption key)")
print("  - Result: 32-byte ChaCha20-Poly1305 key")
print()

print("Step 5: Decrypt with ChaCha20-Poly1305")
print(f"  - Ciphertext: {envelope['ciphertext']}")
print(f"  - Nonce: {envelope['nonce']}")
print("  - Verify MAC tag (ensures no tampering)")
print("  - Decrypt ciphertext by XORing with keystream")
print()

# Decrypt
plaintext = demo.decrypt(priv, envelope)

print(f"  ✓ Decrypted: '{plaintext.decode('utf-8')}'")
print()

print("="*80)
print(" VERIFICATION ")
print("="*80)
print()
print(f"Original:  '{message}'")
print(f"Decrypted: '{plaintext.decode('utf-8')}'")
print()
if message == plaintext.decode('utf-8'):
    print("✓ SUCCESS! Messages match perfectly!")
else:
    print("✗ FAILED! Messages don't match")
print()

print("="*80)
print(" KEY CRYPTOGRAPHIC INSIGHTS ")
print("="*80)
print()
print("1. HYBRID ENCRYPTION (KEM-DEM Pattern)")
print("   KEM (Key Encapsulation Mechanism):")
print("     - X25519 ECDH provides shared secret")
print("     - Ephemeral public key is transmitted in envelope")
print()
print("   DEM (Data Encapsulation Mechanism):")
print("     - ChaCha20-Poly1305 encrypts actual message")
print("     - Uses key derived from shared secret")
print()
print("2. FORWARD SECRECY")
print("   - Each message uses fresh ephemeral key")
print("   - Compromising one message doesn't affect others")
print()
print("3. AUTHENTICATED ENCRYPTION")
print("   - Poly1305 MAC prevents tampering")
print("   - Attacker can't modify ciphertext without detection")
print()
print("4. IDENTITY-BASED KEY DERIVATION")
print("   - Recipient's private key = HKDF(MSK || email)")
print("   - Same email always gets same private key")
print("   - Sender doesn't need recipient's key beforehand!")
print()
print("5. SECURITY PROPERTIES")
print("   ✓ Confidentiality: Only recipient can decrypt")
print("   ✓ Integrity: Tampering is detected")
print("   ✓ Authenticity: MAC verifies message origin")
print("   ✓ Uniqueness: Random nonce ensures different ciphertext")
print()
print("="*80)

# Show what happens if we encrypt the same message again
print()
print("🔄 BONUS: Encrypting Same Message Twice")
print("-" * 80)
print("Let's encrypt 'World is here' again and see what happens...")
print()

envelope2 = demo.encrypt(identity, message.encode('utf-8'))

print("First encryption:")
print(f"  Ciphertext: {envelope['ciphertext']}")
print(f"  Nonce: {envelope['nonce']}")
print()
print("Second encryption:")
print(f"  Ciphertext: {envelope2['ciphertext']}")
print(f"  Nonce: {envelope2['nonce']}")
print()

if envelope['ciphertext'] == envelope2['ciphertext']:
    print("✗ IDENTICAL ciphertext (BAD - deterministic encryption)")
else:
    print("✓ DIFFERENT ciphertext (GOOD - prevents traffic analysis)")
    print("  - Random ephemeral keys ensure uniqueness")
    print("  - Attacker can't tell if same message was sent twice")
print()
print("="*80)
