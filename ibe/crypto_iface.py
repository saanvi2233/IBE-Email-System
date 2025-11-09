"""
Small IBE-like interface and a demo implementation.

This module defines an interface and a demo implementation that issues per-identity
X25519 keypairs from the PKG. The demo lets you run the end-to-end flows locally
without charm-crypto. Replace `DemoIBE` with a real IBE implementation later.
"""
from __future__ import annotations
import os
import base64
import json
import unicodedata
from typing import Tuple, Dict, Any

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305


def b64(b: bytes) -> str:
    return base64.b64encode(b).decode('ascii')


def ub64(s: str) -> bytes:
    return base64.b64decode(s)


def canonicalize_identity(identity: str) -> str:
    """Canonicalize an identity string (email) for consistent usage.
    
    Applies: strip whitespace, lowercase, Unicode NFC normalization.
    Use this in Extract, Encrypt, and all identity lookups to prevent mismatches.
    """
    return unicodedata.normalize('NFC', identity.strip().lower())


class IBEInterface:
    """Defines the small contract used by the demo server and clients."""

    def setup(self) -> Tuple[Dict[str, Any], bytes]:
        """Create MPK and MSK. Returns (mpk, msk_bytes)."""
        raise NotImplementedError()

    def extract(self, msk: bytes, identity: str) -> bytes:
        """Given MSK and an identity, produce a per-identity private key (bytes).

        In the demo this is an X25519 private key serialized in raw bytes.
        """
        raise NotImplementedError()

    def get_pubkey_for_identity(self, identity: str) -> bytes:
        """Return the public key bytes that senders can use for encrypting to identity."""
        raise NotImplementedError()

    def encrypt(self, identity: str, message: bytes) -> Dict[str, Any]:
        """Encrypt message for identity. Returns a dict (ephemeral_pub, ciphertext, nonce).
        Format is JSON-serializable and uses base64 for binary blobs."""
        raise NotImplementedError()

    def decrypt(self, private_key_bytes: bytes, envelope: Dict[str, Any]) -> bytes:
        """Decrypt envelope using the given private key bytes."""
        raise NotImplementedError()


class DemoIBE(IBEInterface):
    """Demo implementation using per-identity X25519 keypairs managed by the PKG.

    NOTE: This is not an actual IBE implementation. It is a runnable demo that
    shows the same high-level flows (Setup, Extract, Encrypt, Decrypt). For a
    real IBE, replace this with a charm-crypto based algorithm.
    """

    def __init__(self, store_path: str = None):
        self.store_path = store_path or os.path.join(os.path.dirname(__file__), '..', 'pkg_data.json')
        self._load()

    def _load(self):
        try:
            with open(self.store_path, 'r', encoding='utf8') as f:
                self.store = json.load(f)
        except Exception:
            self.store = {"identities": {}, "mpk": {}}

    def _save(self):
        with open(self.store_path, 'w', encoding='utf8') as f:
            json.dump(self.store, f, indent=2)

    def setup(self) -> Tuple[Dict[str, Any], bytes]:
        # For demo, mpk contains a random public salt; msk is random bytes kept by server
        msk = os.urandom(32)
        mpk = {"version": 1, "public_salt": b64(os.urandom(16))}
        self.store['mpk'] = mpk
        # We don't persist MSK in the file (server keeps MSK in memory in real run)
        self._save()
        return mpk, msk

    def extract(self, msk: bytes, identity: str) -> bytes:
        # Demo: generate an X25519 keypair for this identity and store public key
        identity = canonicalize_identity(identity)
        if identity in self.store['identities']:
            priv_b64 = self.store['identities'][identity]['priv']
            return ub64(priv_b64)

        private = x25519.X25519PrivateKey.generate()
        public = private.public_key()
        priv_bytes = private.private_bytes(encoding=serialization.Encoding.Raw,
                                           format=serialization.PrivateFormat.Raw,
                                           encryption_algorithm=serialization.NoEncryption())
        pub_bytes = public.public_bytes(encoding=serialization.Encoding.Raw,
                                        format=serialization.PublicFormat.Raw)
        self.store['identities'][identity] = {"pub": b64(pub_bytes), "priv": b64(priv_bytes)}
        self._save()
        return priv_bytes

    def get_pubkey_for_identity(self, identity: str) -> bytes:
        identity = canonicalize_identity(identity)
        ent = self.store['identities'].get(identity)
        if not ent:
            return None
        return ub64(ent['pub'])

    def _derive_key(self, shared: bytes) -> bytes:
        # HKDF to derive a 32-byte AEAD key
        hk = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'demo-ibe')
        return hk.derive(shared)

    def encrypt(self, identity: str, message: bytes) -> Dict[str, Any]:
        identity = canonicalize_identity(identity)
        pub = self.get_pubkey_for_identity(identity)
        if pub is None:
            raise ValueError("unknown identity/public key")
        # Ephemeral X25519 key
        eph_priv = x25519.X25519PrivateKey.generate()
        eph_pub = eph_priv.public_key().public_bytes(encoding=serialization.Encoding.Raw,
                                                     format=serialization.PublicFormat.Raw)
        peer_pub = x25519.X25519PublicKey.from_public_bytes(pub)
        shared = eph_priv.exchange(peer_pub)
        key = self._derive_key(shared)
        aead = ChaCha20Poly1305(key)
        nonce = os.urandom(12)
        ct = aead.encrypt(nonce, message, None)
        return {"ephemeral_pub": b64(eph_pub), "nonce": b64(nonce), "ciphertext": b64(ct)}

    def decrypt(self, private_key_bytes: bytes, envelope: Dict[str, Any]) -> bytes:
        priv = x25519.X25519PrivateKey.from_private_bytes(private_key_bytes)
        eph_pub = ub64(envelope['ephemeral_pub'])
        peer = x25519.X25519PublicKey.from_public_bytes(eph_pub)
        shared = priv.exchange(peer)
        key = self._derive_key(shared)
        aead = ChaCha20Poly1305(key)
        nonce = ub64(envelope['nonce'])
        ct = ub64(envelope['ciphertext'])
        return aead.decrypt(nonce, ct, None)


__all__ = ["IBEInterface", "DemoIBE", "b64", "ub64", "canonicalize_identity"]
