# Security Considerations for IBE Email System

This document outlines the security model, trust assumptions, known limitations, and recommended mitigations for this Identity-Based Encryption (IBE) prototype.

## Trust Model

### Private Key Generator (PKG)
- The PKG is the **most trusted component** in the system.
- It holds the Master Secret Key (MSK) and can generate private keys for any identity.
- **Key Escrow Problem:** The PKG can decrypt any message encrypted to any identity by generating that user's private key. This is a fundamental property of IBE.
- **Mitigation options:**
  - Use a **threshold PKG**: split the MSK among multiple non-colluding parties (e.g., 3-of-5) so no single operator can generate keys alone.
  - Store MSK in a **Hardware Security Module (HSM)** with strict access controls and audit logging.
  - Implement **audit logs** for all Extract operations (protected and monitored).
  - Use organizational policies and legal agreements to enforce PKG operator accountability.

### User Authentication
- The security of the entire system depends on correct authentication before issuing private keys.
- **Current implementation:** Email-based one-time password (OTP) sent to the user's email address.
- **Limitations:**
  - If an attacker compromises the user's email account, they can request and receive the user's private key.
  - Email delivery is not instant and can be intercepted or delayed.
- **Recommended improvements:**
  - Integrate with organizational Identity Providers (IdP) using OAuth2, SAML, or OIDC.
  - Use multi-factor authentication (MFA) before issuing private keys.
  - Implement device-based authentication (e.g., client certificates, hardware tokens).
  - For high-security environments, require in-person verification or signed authorization.

## Data Protection

### Master Secret Key (MSK)
- **Current demo:** MSK is generated at startup and stored in memory only (not persisted).
- **Production requirements:**
  - Store MSK encrypted at rest using a Key Encryption Key (KEK) from an HSM or cloud KMS.
  - Never commit MSK or MSK-encrypted files to version control.
  - Rotate MSK periodically (requires re-issuing all user keys).
  - Implement strict access controls (RBAC) for MSK operations.

### Private Keys (Client-Side)
- **Current demo:** Private keys are returned as base64 strings over HTTPS and clients must store them locally.
- **Risks:** Keys stored in plaintext on disk can be stolen if the device is compromised.
- **Recommended mitigations:**
  - Encrypt private keys client-side using a strong passphrase (Argon2id + AES-GCM) before saving to disk.
  - Use OS-level keystores (Windows DPAPI, macOS Keychain, Linux Secret Service).
  - Implement key derivation from user password so keys are never stored in plaintext.
  - For mobile/web clients, use secure enclave or WebCrypto API with non-extractable keys.

### Ciphertext and Messages
- **Current implementation:** Uses hybrid encryption (KEM-DEM pattern):
  - DemoIBE: X25519 ECDH + HKDF + ChaCha20-Poly1305 AEAD
  - CharmIBE: Boneh-Franklin pairing + HKDF + AEAD (when charm-crypto is used)
- **Security properties:**
  - Authenticated encryption (AEAD) prevents tampering and provides integrity.
  - Forward secrecy is **not** provided in standard IBE (if MSK is compromised, all past messages can be decrypted).
- **Mitigations:**
  - Use time-stamped identities (see revocation below) to limit MSK compromise impact.
  - Combine IBE with forward-secret key exchange (e.g., Signal-style ratcheting) for long-term conversations.

## Key Revocation

- **Problem:** IBE does not natively support revocation. Once a user has their private key, they can decrypt all messages encrypted to their identity until the key expires.
- **Current demo:** No revocation mechanism implemented.
- **Recommended approach: Time-Stamped Identities**
  - Append a time period to the identity string: `alice@example.com|202511` (November 2025).
  - Users must request new keys each period (e.g., monthly).
  - Old keys automatically become invalid for new messages.
  - **Trade-off:** Increases PKG load (more Extract calls) and requires coordination between sender and receiver on the time format.
- **Alternative approaches:**
  - **Certificate Revocation List (CRL):** PKG publishes a list of revoked identities. Senders must check the CRL before encrypting.
  - **Key Update Tokens:** PKG periodically issues update tokens; users must obtain tokens to continue using keys.
  - **Broadcast Revocation:** PKG broadcasts revocation information; clients update local policies.

## Network Security

### Transport Layer
- **Current demo:** Uses HTTP on localhost for testing.
- **Production requirements:**
  - **Always use HTTPS (TLS 1.3)** for all PKG endpoints.
  - Enforce strict certificate validation (pin PKG certificate or use organizational CA).
  - Use HSTS (HTTP Strict Transport Security) to prevent downgrade attacks.
  - Implement rate limiting and DDoS protection at the network edge.

### SMTP Security (for OTP)
- **Current demo:** Supports a local debug SMTP server (no TLS, no auth) for testing.
- **Production requirements:**
  - Use TLS (STARTTLS or implicit TLS) for all SMTP connections.
  - Store SMTP credentials (username/password) securely (env vars, Vault, HSM).
  - Use SPF, DKIM, and DMARC to prevent email spoofing.
  - Monitor SMTP logs for suspicious activity (mass OTP requests, etc.).

## Authentication Flow Security

### OTP Implementation
- **Current settings:**
  - OTP length: 6 digits (10^6 = 1 million possible values)
  - TTL: 600 seconds (10 minutes)
  - Max attempts: 3
- **Security properties:**
  - Brute force: 3 attempts / 10^6 space = low success rate
  - Time-bound: expired OTPs are deleted
- **Known weaknesses:**
  - 6-digit OTPs can be brute-forced if rate limiting is weak.
  - Email delivery can be delayed or intercepted.
- **Mitigations:**
  - Add per-identity and per-IP rate limiting (e.g., max 3 OTP requests per hour per identity).
  - Increase OTP length to 8 digits for higher security environments.
  - Log all OTP requests and verification attempts (monitor for anomalies).
  - Consider using cryptographically signed tokens instead of numeric OTPs (e.g., JWTs with short expiry).

## Audit and Logging

- **What to log:**
  - All Extract operations (identity, timestamp, success/failure)
  - OTP requests and verification attempts (with IP address)
  - MPK access (optional, for monitoring)
  - MSK access/operations (critical)
- **Log protection:**
  - Store logs in append-only storage or send to a SIEM (Security Information and Event Management) system.
  - Encrypt logs at rest.
  - Restrict access to logs (only security team and auditors).
- **Privacy considerations:**
  - Logs contain sensitive identity information (email addresses).
  - Implement data retention policies and comply with GDPR/CCPA where applicable.

## Deployment Checklist

Before deploying this IBE system in production:

- [ ] MSK stored in HSM or encrypted with strong KEK
- [ ] HTTPS with valid certificate (TLS 1.3) enforced
- [ ] Strong user authentication (OAuth/OIDC or MFA)
- [ ] Private keys encrypted client-side before storage
- [ ] OTP rate limiting and IP-based throttling implemented
- [ ] SMTP uses TLS and credentials stored securely
- [ ] Audit logging enabled and monitored
- [ ] Time-stamped identities or revocation mechanism implemented
- [ ] Security review and penetration testing completed
- [ ] Incident response plan documented
- [ ] Regular MSK rotation schedule defined
- [ ] Backup and disaster recovery procedures tested

## Known Limitations (For College Project)

This prototype is designed for educational purposes and demonstration. **Do not use in production without significant hardening.**

- DemoIBE is not a real IBE scheme (uses per-identity X25519 keys managed by PKG).
- MSK is not persisted (regenerated on each server restart).
- OTP storage is in-memory (lost on restart; use Redis or DB in production).
- No rate limiting on endpoints (vulnerable to abuse).
- No monitoring or alerting.
- Single-instance server (no HA/redundancy).

## Further Reading

- **IBE Foundations:** Boneh, D., & Franklin, M. (2001). "Identity-Based Encryption from the Weil Pairing." CRYPTO 2001.
- **Key Escrow:** Schneier, B., "The Risks of Key Recovery, Key Escrow, and Trusted Third-Party Encryption." 1997.
- **Threshold Cryptography:** Shamir, A., "How to Share a Secret." Communications of the ACM, 1979.
- **NIST Guidelines:** NIST SP 800-57 (Key Management) and NIST SP 800-63 (Digital Identity Guidelines).

---

For questions or to report security issues, contact the project maintainer.
