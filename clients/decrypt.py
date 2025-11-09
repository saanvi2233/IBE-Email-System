"""Client script to request a private key (extract) from the PKG and decrypt an envelope."""
from __future__ import annotations
import argparse
import requests
import json
from ibe.crypto_iface import ub64, canonicalize_identity


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pkg', default='http://127.0.0.1:5000')
    p.add_argument('--identity', required=True)
    p.add_argument('--otp', required=True, help='One-time passcode from email')
    p.add_argument('--envelope', required=True, help='JSON string of the envelope')
    args = p.parse_args()

    identity = canonicalize_identity(args.identity)
    # Request private key from PKG
    r = requests.post(args.pkg + '/extract', json={'identity': identity, 'otp': args.otp})
    if r.status_code != 200:
        print('Failed to extract private key:', r.status_code, r.text)
        return
    priv_b64 = r.json()['private_b64']
    priv = ub64(priv_b64)

    env = json.loads(args.envelope)
    from ibe.crypto_iface import DemoIBE
    demo = DemoIBE()
    pt = demo.decrypt(priv, env)
    print(pt.decode('utf8'))


if __name__ == '__main__':
    main()
