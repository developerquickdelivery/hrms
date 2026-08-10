#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Install Ubuntu 24.04 on WSL2 for QD HRMS (Frappe/ERPNext).
.DESCRIPTION
  Run this once in an elevated PowerShell:
    Right-click PowerShell -> Run as administrator
    Set-ExecutionPolicy -Scope Process Bypass
    cd C:\anw\work\QD-HRMS\scripts
    .\01_install_ubuntu_wsl.ps1
#>

$ErrorActionPreference = "Stop"
Write-Host "==> Checking WSL..." -ForegroundColor Cyan

wsl --update
wsl --set-default-version 2

$distros = (wsl -l -q 2>$null) | ForEach-Object { ($_ -replace "`0","").Trim() } | Where-Object { $_ }
$hasUbuntu = $distros | Where-Object { $_ -match "Ubuntu-24.04|Ubuntu" }

if (-not $hasUbuntu) {
  Write-Host "==> Installing Ubuntu-24.04 (this can take several minutes)..." -ForegroundColor Cyan
  wsl --install -d Ubuntu-24.04 --no-launch
  Write-Host "==> Distro registered. Launching first-time setup..." -ForegroundColor Cyan
} else {
  Write-Host "==> Ubuntu already present: $hasUbuntu" -ForegroundColor Green
}

Write-Host ""
Write-Host "NEXT:" -ForegroundColor Yellow
Write-Host "  1. Open 'Ubuntu 24.04 LTS' from the Start menu"
Write-Host "  2. Create your Linux username and password when asked"
Write-Host "  3. Then run:  .\02_copy_and_run_frappe_setup.ps1  (normal PowerShell is fine)"
Write-Host ""
Write-Host "If Windows asked for a reboot earlier, reboot first, then open Ubuntu." -ForegroundColor Yellow
