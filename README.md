# IBE Project Prototype

This repository is a small prototype to demonstrate the high-level flows of an Identity-Based Encryption (IBE) system: a PKG (server) that issues keys, and clients that encrypt and decrypt messages.

**Important:** This prototype includes two backends:
- `DemoIBE` (in `ibe/crypto_iface.py`): Uses per-identity X25519 keypairs issued by the PKG. This is a runnable demo that shows end-to-end flows without installing heavy crypto libraries. **This is NOT a real IBE scheme.**
- `CharmIBE` (in `ibe/charm_impl.py`): A real Boneh-Franklin IBE implementation using `charm-crypto`. Requires installation of charm-crypto (see below).

What's included
- `pkg/server.py` — Flask PKG with `/mpk`, `/get_pubkey`, `/request_extract_code`, and `/extract` endpoints.
- `pkg/auth_otp.py` — Email-based one-time password (OTP) authentication for Extract.
- `clients/encrypt.py` — command-line client to encrypt a message for an identity.
- `clients/decrypt.py` — client to request a private key (via OTP) and decrypt a ciphertext.
- `ibe/crypto_iface.py` — interface + `DemoIBE` implementation with identity canonicalization.
- `ibe/charm_impl.py` — Boneh-Franklin IBE using charm-crypto (optional).
- `tests/` — pytest unit tests for canonicalization, OTP flow, and roundtrip encryption.
- `requirements.txt` — Python deps for the demo.

## Run the demo locally (Windows PowerShell)

### 1. Create a virtualenv and install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Start a debug SMTP server (for OTP emails)

In a separate terminal, run a local SMTP debug server that prints emails to stdout:

```powershell
python scripts\debug_smtp_server.py --port 1025
```

This will print all OTP codes sent by the PKG to the console. In production, configure a real SMTP server via environment variables (see Configuration section below).

### 3. Start the PKG server

In another terminal (with the venv activated):

```powershell
.\.venv\Scripts\Activate.ps1
python pkg\server.py
```

The server starts on `http://127.0.0.1:5000`.

### 4. Request an OTP for alice@example.com

In another terminal:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/request_extract_code -Body (@{identity='alice@example.com'} | ConvertTo-Json) -ContentType 'application/json'
```

Check the debug SMTP terminal — it will print the 6-digit OTP.

### 5. Extract the private key using the OTP

Copy the OTP from the SMTP debug output and use it to call `/extract`:

```powershell
$response = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/extract -Body (@{identity='alice@example.com'; otp='123456'} | ConvertTo-Json) -ContentType 'application/json'
$response
```

This returns Alice's private key (base64 encoded). Save it for decryption.

### 6. Encrypt a message for alice@example.com

```powershell
python clients\encrypt.py --identity alice@example.com --message "Hello Alice"
```

This prints a JSON envelope with the ciphertext. Copy the entire JSON output.

### 7. Decrypt the message using the private key

```powershell
python clients\decrypt.py --identity alice@example.com --otp 123456 --envelope '{"ephemeral_pub":"...","nonce":"...","ciphertext":"..."}'
```

(Use the OTP you received earlier, or request a new one before running decrypt.)

The decrypted message is printed to stdout.

### 8. Run tests

```powershell
pytest -q
```

All tests should pass.

## Configuration (environment variables)

The server and OTP module use environment variables for configuration:

### SMTP configuration (for OTP emails)
- `SMTP_HOST` — SMTP server host (default: `localhost`)
- `SMTP_PORT` — SMTP server port (default: `1025` for debug server)
- `SMTP_USER` — SMTP username (optional)
- `SMTP_PASS` — SMTP password (optional)
- `SMTP_FROM_EMAIL` — sender email address (default: `noreply@ibe-pkg.local`)

### OTP settings
- `OTP_TTL_SECONDS` — OTP lifetime in seconds (default: `600` = 10 minutes)
- `OTP_MAX_ATTEMPTS` — maximum failed verification attempts before lockout (default: `3`)

### PKG backend selection
- `USE_CHARM=1` — use charm-crypto IBE backend instead of DemoIBE (requires charm-crypto installed)
- `PKG_PORT` — server port (default: `5000`)

Example PowerShell usage:

```powershell
$env:SMTP_HOST = 'smtp.gmail.com'
$env:SMTP_PORT = '587'
$env:SMTP_USER = 'your-email@gmail.com'
$env:SMTP_PASS = 'your-app-password'
$env:SMTP_FROM_EMAIL = 'your-email@gmail.com'
python pkg\server.py
```

## Notes and limitations

- **DemoIBE is not real IBE:** It uses per-identity X25519 keypairs managed by the PKG. This demonstrates API flows, AEAD usage, and testing, but is not cryptographically equivalent to IBE.
- **Key escrow:** The PKG can generate any user's private key (fundamental to IBE). In production, use a threshold PKG, HSM, or strong audit logging.
- **OTP authentication:** Email-based OTP is acceptable for a college project but has limitations (email account compromise). For production, use OAuth/OIDC or a verified email flow with organizational IdP.
- **Private key storage:** Demo returns raw private keys over HTTPS. In production, encrypt client-side (Argon2 + AES-GCM) or use OS keystores.
- **Revocation:** Demo lacks revocation. Recommended approach: use time-stamped identities (e.g., `alice@example.com|202511`) so keys expire monthly.
- **Data storage:** Demo stores keys in `pkg_data.json` in the server directory. Do not use this for production; use encrypted storage or HSM.

Charm-crypto notes
------------------
If you want a real IBE backend (e.g., Boneh-Franklin) we can use `charm-crypto`. A few notes:

- `charm-crypto` can be difficult to install on native Windows. For best results install it in WSL/Ubuntu or a Linux environment.
- Typical install steps on Ubuntu/WSL:

```bash
sudo apt update
sudo apt install -y build-essential python3-dev libgmp-dev libssl-dev
pip install charm-crypto
```

- After installing, set the environment variable `USE_CHARM=1` before starting the PKG server to switch to the charm backend.

If you want, I can add a fully implemented `CharmIBE` in `ibe/charm_stub.py` once you confirm `charm-crypto` is available or allow me to provide a small install script for WSL.

Install helper scripts
----------------------
I added two helper scripts under `scripts/` to make installation easier on Windows (via WSL):

- `scripts/install_charm_wsl.sh` — Bash script to run inside WSL/Ubuntu. It installs required system packages, creates a virtualenv named `.venv_charm`, and installs `charm-crypto` into that venv.
- `scripts/install_charm_wsl.ps1` — PowerShell helper that attempts to invoke the above script inside WSL from Windows.

Usage (Windows + WSL recommended):

1. Open PowerShell in the repository root and run the helper (this will call WSL):

```powershell
.\scripts\install_charm_wsl.ps1
```

2. Alternatively, open your WSL shell (Ubuntu) and run directly from the project directory:

```bash
bash scripts/install_charm_wsl.sh
```

3. After installation activate the venv in WSL before running server/tests:

```bash
. .venv_charm/bin/activate
export USE_CHARM=1
python -m pytest -q
```

If any of these steps fail I can help debug the install errors — paste the failing output and I'll provide fixes.
