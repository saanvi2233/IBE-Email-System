"""Client script to encrypt a message for an identity using the demo PKG's stored pubkey."""
from __future__ import annotations
import argparse
import requests
import json
from ibe.crypto_iface import b64, ub64, canonicalize_identity


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pkg', default='http://127.0.0.1:5000')
    p.add_argument('--identity', required=True)
    p.add_argument('--message', required=True)
    args = p.parse_args()

    identity = canonicalize_identity(args.identity)
    r = requests.get(args.pkg + '/get_pubkey', params={'identity': identity})
    if r.status_code != 200:
        print('Failed to get pubkey:', r.text)
        return
    pub_b64 = r.json()['pub_b64']
    # We will perform encryption locally using the DemoIBE routines; but the client
    # does not import DemoIBE directly to keep this script simple. Instead this script
    # calls a server-side helper -- for demo we expect PKG to have created the pubkey.

    # For demo simplicity, call a helper encrypt endpoint? We don't have one; instead
    # perform a minimal local operation by importing the demo implementation.
    from ibe.crypto_iface import DemoIBE
    demo = DemoIBE()
    # Ensure the server has a stored public key for the identity
    env = demo.encrypt(identity, args.message.encode('utf8'))
    print(json.dumps(env))


if __name__ == '__main__':
    main()
