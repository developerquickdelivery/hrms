<#
.SYNOPSIS
  Copy Frappe setup script into Ubuntu WSL and start it.
.DESCRIPTION
  Run AFTER Ubuntu is installed and your Linux user exists.
  Normal (non-admin) PowerShell is fine.
#>

$ErrorActionPreference = "Stop"
$Distro = "Ubuntu-24.04"
$WinScript = "C:\anw\work\QD-HRMS\scripts\setup_frappe_wsl.sh"

Write-Host "==> Verifying distro $Distro ..." -ForegroundColor Cyan
$raw = wsl -l -q 2>$null | ForEach-Object { ($_ -replace "`0","").Trim() }
if (-not ($raw | Where-Object { $_ -eq $Distro })) {
  # fallback to first Ubuntu*
  $fallback = $raw | Where-Object { $_ -match "^Ubuntu" } | Select-Object -First 1
  if (-not $fallback) {
    throw "No Ubuntu distro found. Run scripts\01_install_ubuntu_wsl.ps1 as Administrator first."
  }
  $Distro = $fallback
  Write-Host "    Using distro: $Distro" -ForegroundColor Yellow
}

if (-not (Test-Path $WinScript)) {
  throw "Missing setup script: $WinScript"
}

Write-Host "==> Copying setup script into WSL home..." -ForegroundColor Cyan
wsl -d $Distro -e bash -lc "mkdir -p ~/qd-hrms-setup && cp /mnt/c/anw/work/QD-HRMS/scripts/setup_frappe_wsl.sh ~/qd-hrms-setup/ && chmod +x ~/qd-hrms-setup/setup_frappe_wsl.sh && ls -la ~/qd-hrms-setup"

Write-Host ""
Write-Host "==> Starting Frappe/ERPNext/HRMS + qd_hrms install inside WSL..." -ForegroundColor Cyan
Write-Host "    Linux user: qd   password: qd1234  (sudo; typing is hidden)" -ForegroundColor Yellow
Write-Host "    This takes 20-40 minutes. Stay in WSL for 'bench start' after." -ForegroundColor Yellow
Write-Host ""

wsl -d $Distro -e bash -lc "export HOME=/home/qd; cd /home/qd/qd-hrms-setup && bash setup_frappe_wsl.sh"
if ($LASTEXITCODE -ne 0) {
  Write-Host ""
  Write-Host "SETUP FAILED (exit $LASTEXITCODE). Do not run bench start yet." -ForegroundColor Red
  Write-Host "If sudo failed, password for user qd is: qd1234" -ForegroundColor Yellow
  exit $LASTEXITCODE
}

Write-Host ""
Write-Host "DONE. In a NEW terminal run:" -ForegroundColor Green
Write-Host "  wsl -d $Distro"
Write-Host "  cd ~/frappe-bench && bench start"
Write-Host "Then open http://127.0.0.1:8000  (Administrator / admin)"
Write-Host "Note: ~/frappe-bench only exists INSIDE Ubuntu/WSL, not in PowerShell."
