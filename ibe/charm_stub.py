"""Charm-crypto IBE stub and usage example.

This module attempts to import a Boneh-Franklin IBE implementation from
`charm-crypto` and expose the same interface used by `DemoIBE` in
`ibe.crypto_iface`. If `charm-crypto` is not available, the module provides
clear instructions and raises ImportError when used.

To use a real IBE backend:
 - Install charm-crypto on Linux or WSL (recommended for Windows users).
 - Set the environment variable `USE_CHARM=1` before starting `pkg/server.py`.

The code below is a template — verify the exact `charm` scheme import names
on your environment (they can differ between charm versions). This stub will
be replaced by a fully tested class after you install charm-crypto.
"""
from __future__ import annotations
import os

try:
    # Try importing a common Boneh-Franklin implementation in charm
    from charm.toolbox.pairinggroup import PairingGroup
    from charm.schemes.ibenc.ibenc_bf01 import IBE_BF01
except Exception as e:
    # Provide a helpful error if charm isn't installed
    PairingGroup = None
    IBE_BF01 = None
    _import_error = e


class CharmIBE:
    """Thin wrapper around charm's BF-IBE implementing the DemoIBE contract.

    NOTE: This class is a template and untested here. After installing
    `charm-crypto` you can use this class to perform SetUp/Extract/Encrypt/Decrypt.
    """

    def __init__(self, group_name: str = 'SS512'):
        if PairingGroup is None or IBE_BF01 is None:
            raise ImportError(
                'charm-crypto not available. Install charm-crypto or run demo backend. Original error: %s' % _import_error
            )
        self.group = PairingGroup(group_name)
        self.ibe = IBE_BF01(self.group)
        self.mpk = None
        self.msk = None

    def setup(self):
        mpk, msk = self.ibe.setup()
        self.mpk = mpk
        self.msk = msk
        # Serialize mpk in a JSON-friendly manner; exact representation depends on charm
        return {'version': 1, 'mpk': str(mpk)}, self.msk

    def extract(self, msk: bytes, identity: str) -> bytes:
        # charm's extract returns a private key object; you must serialize it
        sk = self.ibe.extract(msk, identity)
        # Example: use charm serialization utilities (not shown here)
        return sk

    def get_pubkey_for_identity(self, identity: str) -> bytes:
        # IBE is identity-based; typically there is no per-identity public key
        # to distribute beyond using the MPK and the plain identity string.
        # We return a placeholder to match the DemoIBE interface.
        return b''

    def encrypt(self, identity: str, message: bytes):
        # The charm scheme's encrypt expects plaintext in a specific format.
        # Use the scheme's api: self.ibe.encrypt(self.mpk, identity, message)
        ct = self.ibe.encrypt(self.mpk, identity, message)
        return {'charm_ct': ct}

    def decrypt(self, private_key_bytes: bytes, envelope: dict) -> bytes:
        # Convert serialized private key back to charm object, then decrypt
        sk = private_key_bytes
        ct = envelope['charm_ct']
        pt = self.ibe.decrypt(self.mpk, sk, ct)
        return pt


def charm_available() -> bool:
    return PairingGroup is not None and IBE_BF01 is not None


def install_notes() -> str:
    return (
        'charm-crypto installation is platform-dependent. On Windows use WSL/Ubuntu and run:\n'
        '  sudo apt update; sudo apt install -y build-essential python3-dev libgmp-dev libssl-dev\n'
        '  pip install charm-crypto\n'
        'If pip install fails, follow charm-crypto repo build instructions: https://github.com/JHUISI/charm'
    )


__all__ = ['CharmIBE', 'charm_available', 'install_notes']
