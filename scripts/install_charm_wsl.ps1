<#
PowerShell helper to run the WSL install script from Windows.

This script will:
- Print instructions and attempt to call WSL to run the bash installer.

It does not modify your system. It attempts to run the WSL script located at the
project path. If you prefer, open WSL manually and run `bash scripts/install_charm_wsl.sh`.
#>
param()

$repoPath = Convert-Path .
Write-Host "Repository path: $repoPath"

if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
    Write-Host "WSL not found on this machine. Please enable WSL and install a Linux distro (e.g., Ubuntu) from the Microsoft Store." -ForegroundColor Yellow
    Write-Host "Alternatively, run the installer manually inside a Linux environment." -ForegroundColor Yellow
    exit 1
}

# Convert Windows path to WSL path: /mnt/<drive_letter>/<path>
$drive = $repoPath.Substring(0,1).ToLower()
$rest = $repoPath.Substring(2) -replace '\\','/'
$wslPath = "/mnt/$drive/$rest"

Write-Host "Attempting to run installer in WSL at: $wslPath/scripts/install_charm_wsl.sh"
Write-Host "You may be prompted for your Linux password for sudo during the install."

wsl bash -lc "cd '$wslPath' && bash scripts/install_charm_wsl.sh"

Write-Host "If the above command failed, open WSL (Ubuntu) and run: cd $wslPath; bash scripts/install_charm_wsl.sh"
