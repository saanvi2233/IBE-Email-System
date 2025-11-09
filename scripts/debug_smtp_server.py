"""Simple SMTP debug server for testing OTP emails.

This is a replacement for `python -m smtpd` which was removed in Python 3.12.
It prints all received emails to stdout, making it easy to see OTP codes during testing.

Requires: aiosmtpd (install via requirements.txt)

Usage:
    python scripts/debug_smtp_server.py [--host HOST] [--port PORT]

Example:
    python scripts/debug_smtp_server.py --port 1025
"""
import asyncio
import argparse
from aiosmtpd.controller import Controller


class DebugHandler:
    """Handler that prints all received messages."""
    
    async def handle_DATA(self, server, session, envelope):
        """Called when a complete message is received."""
        print('=' * 70)
        print(f'From: {envelope.mail_from}')
        print(f'To: {", ".join(envelope.rcpt_tos)}')
        print(f'Peer: {session.peer}')
        print('-' * 70)
        # Decode and print message content
        if isinstance(envelope.content, bytes):
            print(envelope.content.decode('utf-8', errors='replace'))
        else:
            print(envelope.content)
        print('=' * 70)
        print()
        return '250 Message accepted for delivery'


def main():
    parser = argparse.ArgumentParser(description='Debug SMTP server for testing OTP emails')
    parser.add_argument('--host', default='localhost', help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=1025, help='Port to bind to (default: 1025)')
    args = parser.parse_args()
    
    print(f'Starting debug SMTP server on {args.host}:{args.port}')
    print('All received emails will be printed below.')
    print('Press Ctrl+C to stop')
    print()
    
    handler = DebugHandler()
    controller = Controller(handler, hostname=args.host, port=args.port)
    controller.start()
    
    try:
        # Keep running until interrupted
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print('\nShutting down server...')
        controller.stop()


if __name__ == '__main__':
    main()
