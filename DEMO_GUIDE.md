# End-to-End Demo Guide

This guide walks you through a complete demonstration of the IBE email system.

## Prerequisites

1. Install dependencies:
```powershell
pip install -r requirements.txt
```

2. You should have 2-3 terminal windows open.

## Step-by-Step Demo

### Terminal 1: Start Debug SMTP Server

This server will print OTP codes that would normally be emailed.

```powershell
python scripts\debug_smtp_server.py --port 1025
```

**Expected output:**
```
Starting debug SMTP server on localhost:1025
All received emails will be printed below.
Press Ctrl+C to stop
```

Leave this running and watch for OTP codes.

---

### Terminal 2: Start PKG Server

```powershell
$env:PYTHONPATH = "d:\OneDrive\Documents\cypto_proj"
python pkg\server.py
```

**Expected output:**
```
Starting demo PKG on http://127.0.0.1:5000
 * Running on http://127.0.0.1:5000
```

Leave this running.

---

### Terminal 3: Run the Demo Flow

#### Step 1: Request an OTP for Alice

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/request_extract_code `
  -Body (@{identity='alice@example.com'} | ConvertTo-Json) `
  -ContentType 'application/json'
```

**Expected response:**
```json
{
  "status": "otp_sent",
  "identity": "alice@example.com"
}
```

**Check Terminal 1** - you should see an email printed with a 6-digit OTP code like `123456`.

---

#### Step 2: Extract Alice's Private Key using the OTP

Replace `123456` with the actual OTP from Terminal 1:

```powershell
$response = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/extract `
  -Body (@{identity='alice@example.com'; otp='123456'} | ConvertTo-Json) `
  -ContentType 'application/json'

$response
```

**Expected response:**
```json
{
  "identity": "alice@example.com",
  "private_b64": "BASE64_ENCODED_PRIVATE_KEY..."
}
```

Save this for later or keep the variable in your session.

---

#### Step 3: Encrypt a Message for Alice

Bob wants to send Alice a secret message:

```powershell
python clients\encrypt.py --identity alice@example.com --message "Hello Alice, this is a secret!"
```

**Expected output:**
```json
{
  "ephemeral_pub": "...",
  "nonce": "...",
  "ciphertext": "..."
}
```

**Copy the entire JSON output** (you'll need it for decryption).

---

#### Step 4: Decrypt the Message

Alice receives the encrypted message and wants to decrypt it.

Option A: Request a new OTP and use the decrypt client:

```powershell
# Request new OTP
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/request_extract_code `
  -Body (@{identity='alice@example.com'} | ConvertTo-Json) `
  -ContentType 'application/json'

# Check Terminal 1 for new OTP, then decrypt
python clients\decrypt.py --identity alice@example.com --otp NEW_OTP `
  --envelope '{"ephemeral_pub":"...","nonce":"...","ciphertext":"..."}'
```

Option B: Use Python directly (for demo purposes):

```powershell
python -c @"
from ibe.crypto_iface import DemoIBE, ub64
import json

demo = DemoIBE()
envelope = json.loads('PASTE_ENVELOPE_JSON_HERE')
private_b64 = 'PASTE_PRIVATE_KEY_FROM_STEP2'
priv = ub64(private_b64)
plaintext = demo.decrypt(priv, envelope)
print(plaintext.decode('utf-8'))
"@
```

**Expected output:**
```
Hello Alice, this is a secret!
```

---

## Quick Demo Script (All-in-One)

If you want to run everything programmatically without manual steps, use this script:

```powershell
# Demo script - run this after starting SMTP and PKG servers
Write-Host "=== IBE Email System Demo ===" -ForegroundColor Cyan
Write-Host

# 1. Request OTP
Write-Host "[Step 1] Requesting OTP for alice@example.com..." -ForegroundColor Yellow
$otpResp = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/request_extract_code `
  -Body (@{identity='alice@example.com'} | ConvertTo-Json) `
  -ContentType 'application/json'
Write-Host "Status: $($otpResp.status)" -ForegroundColor Green
Write-Host

# 2. Manual step: get OTP from Terminal 1
Write-Host "[Step 2] Check your SMTP debug terminal for the 6-digit OTP code" -ForegroundColor Yellow
$otp = Read-Host "Enter the OTP code"
Write-Host

# 3. Extract private key
Write-Host "[Step 3] Extracting private key with OTP..." -ForegroundColor Yellow
$extractResp = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/extract `
  -Body (@{identity='alice@example.com'; otp=$otp} | ConvertTo-Json) `
  -ContentType 'application/json'
Write-Host "Private key received: $($extractResp.private_b64.Substring(0,20))..." -ForegroundColor Green
Write-Host

# 4. Encrypt message
Write-Host "[Step 4] Encrypting message for alice@example.com..." -ForegroundColor Yellow
$envelope = python clients\encrypt.py --identity alice@example.com --message "Demo secret message!" | ConvertFrom-Json
Write-Host "Ciphertext created" -ForegroundColor Green
Write-Host

# 5. Decrypt message
Write-Host "[Step 5] Decrypting message..." -ForegroundColor Yellow
$plaintext = python -c @"
from ibe.crypto_iface import DemoIBE, ub64
import json
demo = DemoIBE()
envelope = json.loads('$($envelope | ConvertTo-Json -Compress)')
priv = ub64('$($extractResp.private_b64)')
plaintext = demo.decrypt(priv, envelope)
print(plaintext.decode('utf-8'))
"@
Write-Host "Decrypted message: '$plaintext'" -ForegroundColor Green
Write-Host

Write-Host "=== Demo Complete ===" -ForegroundColor Cyan
```

Save this as `demo_script.ps1` and run it after starting the SMTP and PKG servers.

---

## Troubleshooting

### SMTP server shows "no current event loop" warning
This is harmless - the server is still working fine.

### PKG server can't find 'ibe' module
Set PYTHONPATH before running:
```powershell
$env:PYTHONPATH = "d:\OneDrive\Documents\cypto_proj"
```

### OTP not appearing in SMTP terminal
- Make sure the SMTP server is running on port 1025
- Check for errors in the PKG server terminal

### Tests fail
Run pytest to check:
```powershell
python -m pytest tests/ -v
```

All tests should pass.

---

## For Your College Presentation

1. **Start with the security talk**: Explain key escrow, PKG trust, authentication
2. **Show the architecture diagram**: PKG (Setup/Extract) ↔ Clients (Encrypt/Decrypt)
3. **Live demo**: Run through Steps 1-4 above while explaining each step
4. **Discuss trade-offs**: Revocation, authentication weaknesses, mitigations
5. **Show code highlights**: canonicalization, OTP flow, AEAD usage
6. **Point to documentation**: README.md, SECURITY.md, tests

Good luck with your presentation! 🎉
