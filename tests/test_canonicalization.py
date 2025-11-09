"""Test identity canonicalization."""
from ibe.crypto_iface import canonicalize_identity


def test_canonicalize_identity():
    # Test trimming
    assert canonicalize_identity('  alice@example.com  ') == 'alice@example.com'
    # Test lowercasing
    assert canonicalize_identity('Alice@Example.COM') == 'alice@example.com'
    # Test Unicode normalization (combining vs precomposed)
    # e with acute: é (U+00E9) vs e + combining acute (U+0065 U+0301)
    composed = '\u00e9'  # é
    decomposed = 'e\u0301'  # e + combining acute
    assert canonicalize_identity(f'test{composed}@example.com') == canonicalize_identity(f'test{decomposed}@example.com')
    # Combined test
    assert canonicalize_identity('  Alice@EXAMPLE.com  ') == 'alice@example.com'
