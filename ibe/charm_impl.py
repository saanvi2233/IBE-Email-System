"""Boneh-Franklin IBE implementation using charm-crypto.

This module provides a `CharmIBE` class with the same small contract used by
the demo (`setup`, `extract`, `get_pubkey_for_identity`, `encrypt`, `decrypt`).

It serializes charm objects to base64 so they can be transported over JSON.

Note: charm-crypto must be installed (use the WSL installer provided in
`scripts/install_charm_wsl.sh` on Windows). If charm is not available this
module will raise ImportError when used.
"""
from __future__ import annotations
import base64
import json
import os
from typing import Any, Dict, Tuple

try:
    from charm.toolbox.pairinggroup import PairingGroup
    from charm.schemes.ibenc.ibenc_bf01 import IBE_BF01
    from charm.core.engine.util import objectToBytes, bytesToObject
except Exception as e:
    raise ImportError("charm-crypto is required for ibe.charm_impl: %s" % e)


def b64(b: bytes) -> str:
    return base64.b64encode(b).decode('ascii')


def ub64(s: str) -> bytes:
    return base64.b64decode(s)


class CharmIBE:
    """Boneh-Franklin IBE wrapper.

    Usage:
        ibe = CharmIBE(group_name='SS512')
        mpk, msk = ibe.setup()
        # mpk is JSON-serializable dict with base64 fields
        sk_bytes = ibe.extract(msk, 'alice@example.com')  # base64-encoded serialized sk
        ct = ibe.encrypt('alice@example.com', b'hello')
        pt = ibe.decrypt(sk_bytes, ct)

    """

    def __init__(self, group_name: str = 'SS512'):
        self.group = PairingGroup(group_name)
        self.ibe = IBE_BF01(self.group)

    def setup(self) -> Tuple[Dict[str, Any], bytes]:
        mpk, msk = self.ibe.setup()
        # Serialize mpk and msk to base64 so they can be stored/transferred
        mpk_bytes = objectToBytes(mpk, self.group)
        msk_bytes = objectToBytes(msk, self.group)
        mpk_blob = {"version": 1, "mpk_b64": b64(mpk_bytes), "group": str(self.group.param_id())}
        # Return mpk as dict and msk as raw bytes (caller should keep msk secret)
        return mpk_blob, msk_bytes

    def extract(self, msk_bytes: bytes, identity: str) -> str:
        # Convert msk bytes back to charm object
        msk = bytesToObject(msk_bytes, self.group)
        sk = self.ibe.extract(msk, identity)
        sk_bytes = objectToBytes(sk, self.group)
        return b64(sk_bytes)

    def get_pubkey_for_identity(self, identity: str) -> bytes:
        # IBE uses identity string + MPK; there is no separate per-identity pubkey
        # Return empty to keep interface compatible with DemoIBE
        return b''

    def encrypt(self, identity: str, message: bytes) -> Dict[str, Any]:
        # The charm IBE encrypt method returns a ciphertext (scheme-specific)
        # We'll serialize it with objectToBytes and base64 encode for JSON transport
        # Note: charm's encrypt expects a plaintext element or bytes; we pass bytes.
        # First ensure MPK is available on the ibe instance (this wrapper assumes setup was called).
        # The underlying BF scheme expects mpk to have been provided at setup time.
        ct = self.ibe.encrypt(self.ibe.master_public_key, identity, message)
        ct_bytes = objectToBytes(ct, self.group)
        return {"charm_ct_b64": b64(ct_bytes)}

    def decrypt(self, sk_b64: str, envelope: Dict[str, Any]) -> bytes:
        sk_bytes = ub64(sk_b64)
        sk = bytesToObject(sk_bytes, self.group)
        ct_bytes = ub64(envelope['charm_ct_b64'])
        ct = bytesToObject(ct_bytes, self.group)
        pt = self.ibe.decrypt(self.ibe.master_public_key, sk, ct)
        # Depending on charm scheme, `pt` may be bytes or a charm object; ensure bytes
        if isinstance(pt, bytes):
            return pt
        try:
            # attempt to coerce to bytes
            return bytes(pt)
        except Exception:
            # fallback: serialize
            return objectToBytes(pt, self.group)


__all__ = ['CharmIBE']
