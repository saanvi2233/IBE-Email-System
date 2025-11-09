# IBE Email System - Interactive Demo Script
# This script demonstrates the complete IBE flow
# Prerequisites: SMTP debug server and PKG server must be running

# Set PYTHONPATH so Python can find the ibe module
$env:PYTHONPATH = "d:\OneDrive\Documents\cypto_proj"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   Identity-Based Encryption for Email Systems - Demo" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Make sure you have started:" -ForegroundColor Yellow
Write-Host "  1. SMTP debug server: python scripts\debug_smtp_server.py --port 1025" -ForegroundColor Gray
Write-Host "  2. PKG server: python pkg\server.py (with PYTHONPATH set)" -ForegroundColor Gray
Write-Host ""
$ready = Read-Host "Are both servers running? (y/n)"
if ($ready -ne 'y') {
    Write-Host "Please start the servers first. See DEMO_GUIDE.md for instructions." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Step 1: Request OTP for sanvimps@gmail.com" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

try {
    $otpResp = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/request_extract_code `
        -Body (@{identity='sanvimps@gmail.com'} | ConvertTo-Json) `
        -ContentType 'application/json' -ErrorAction Stop
    
    Write-Host "[OK] OTP request sent successfully" -ForegroundColor Green
    Write-Host "  Status: $($otpResp.status)" -ForegroundColor Gray
    Write-Host "  Identity: $($otpResp.identity)" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] Failed to request OTP: $_" -ForegroundColor Red
    Write-Host "  Make sure the PKG server is running on port 5000" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Step 2: Get OTP from SMTP Debug Terminal" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check your SMTP debug server terminal." -ForegroundColor Yellow
Write-Host "You should see an email with a 6-digit OTP code." -ForegroundColor Yellow
Write-Host ""
$otp = Read-Host "Enter the 6-digit OTP code"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Step 3: Extract Private Key with OTP" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

try {
    $extractResp = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/extract `
        -Body (@{identity='sanvimps@gmail.com'; otp=$otp} | ConvertTo-Json) `
        -ContentType 'application/json' -ErrorAction Stop
    
    Write-Host "[OK] Private key extracted successfully" -ForegroundColor Green
    Write-Host "  Identity: $($extractResp.identity)" -ForegroundColor Gray
    Write-Host "  Private key (first 40 chars): $($extractResp.private_b64.Substring(0, [Math]::Min(40, $extractResp.private_b64.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] Failed to extract private key: $_" -ForegroundColor Red
    Write-Host "  Check that the OTP is correct and not expired" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Step 4: Encrypt Message for Sanvi" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$message = Read-Host "Enter a secret message to send to Sanvi"

try {
    $envelopeJson = python clients\encrypt.py --identity sanvimps@gmail.com --message $message 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Encryption failed"
    }
    $envelope = $envelopeJson | ConvertFrom-Json
    
    Write-Host "[OK] Message encrypted successfully" -ForegroundColor Green
    Write-Host "  Ciphertext (first 60 chars): $($envelope.ciphertext.Substring(0, [Math]::Min(60, $envelope.ciphertext.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] Failed to encrypt message: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Step 5: Decrypt Message with Private Key" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

try {
    $envelopeCompact = $envelope | ConvertTo-Json -Compress
    $privateKeyB64 = $extractResp.private_b64
    
    # Create a temporary Python script for decryption
    $tempPy = [System.IO.Path]::GetTempFileName() + ".py"
    
    # Build Python script using single quotes to avoid PowerShell parsing
    $line1 = 'from ibe.crypto_iface import DemoIBE, ub64'
    $line2 = 'import json'
    $line3 = 'demo = DemoIBE()'
    $line4 = "envelope_str = r'''$envelopeCompact'''"
    $line5 = 'envelope = json.loads(envelope_str)'
    $line6 = "priv = ub64('$privateKeyB64')"
    $line7 = 'plaintext = demo.decrypt(priv, envelope)'
    $line8 = 'print(plaintext.decode("utf-8"))'
    
    $pyScript = "$line1`n$line2`n$line3`n$line4`n$line5`n$line6`n$line7`n$line8"
    $pyScript | Out-File -FilePath $tempPy -Encoding utf8
    
    $decrypted = python $tempPy 2>&1
    Remove-Item $tempPy -ErrorAction SilentlyContinue
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to decrypt message: $decrypted" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[OK] Message decrypted successfully" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Original message: '$message'" -ForegroundColor Yellow
    Write-Host "  Decrypted message: '$decrypted'" -ForegroundColor Green
    Write-Host ""
    
    $trimmedDecrypted = $decrypted.Trim()
    if ($message -eq $trimmedDecrypted) {
        Write-Host "[OK] Verification: Messages match!" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Messages do not match" -ForegroundColor Red
    }
} catch {
    Write-Host "[ERROR] Failed to decrypt message: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Demo Complete!" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary of what happened:" -ForegroundColor Yellow
Write-Host "  1. Bob requested an OTP to authenticate as Sanvi" -ForegroundColor Gray
Write-Host "  2. PKG sent OTP to sanvimps@gmail.com (printed in SMTP debug)" -ForegroundColor Gray
Write-Host "  3. Sanvi verified her identity with the OTP" -ForegroundColor Gray
Write-Host "  4. PKG issued Sanvi's private key" -ForegroundColor Gray
Write-Host "  5. Bob encrypted a message using Sanvi's identity (no key exchange needed)" -ForegroundColor Gray
Write-Host "  6. Sanvi decrypted the message using her private key" -ForegroundColor Gray
Write-Host ""
Write-Host "Key IBE benefits demonstrated:" -ForegroundColor Yellow
Write-Host "  [+] No need to exchange public keys beforehand" -ForegroundColor Green
Write-Host "  [+] Email address used directly as public key" -ForegroundColor Green
Write-Host "  [+] PKG manages key distribution" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps for your project:" -ForegroundColor Yellow
Write-Host "  - Review SECURITY.md for security considerations" -ForegroundColor Gray
Write-Host "  - Read implementation details in IMPLEMENTATION_SUMMARY.md" -ForegroundColor Gray
Write-Host "  - Run tests: python -m pytest tests/ -v" -ForegroundColor Gray
Write-Host ""
