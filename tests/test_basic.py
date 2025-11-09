"""Pytest for the demo IBE flows (end-to-end using DemoIBE)."""
from ibe.crypto_iface import DemoIBE


def test_encrypt_decrypt_roundtrip(tmp_path):
    demo = DemoIBE(store_path=str(tmp_path / 'pkg_data.json'))
    mpk, msk = demo.setup()
    identity = 'alice@example.com'
    # Extract private key (PKG action)
    priv = demo.extract(msk, identity)
    # Ensure pubkey is available to sender
    pub = demo.get_pubkey_for_identity(identity)
    assert pub is not None
    msg = b'Hello from test'
    env = demo.encrypt(identity, msg)
    out = demo.decrypt(priv, env)
    assert out == msg
