#!/usr/bin/env bash
# Share local ERPNext (qd.local:8000) with a manager via ngrok.
# Usage:
#   1) Get token: https://dashboard.ngrok.com/get-started/your-authtoken
#   2) ngrok config add-authtoken YOUR_TOKEN
#   3) bash ~/.../start_ngrok_qd.sh
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

if ! command -v ngrok >/dev/null 2>&1; then
  echo "ngrok not found. Run: bash /mnt/c/anw/work/QD-HRMS/scripts/install_ngrok_wsl.sh"
  exit 1
fi

if ! curl -fsS http://127.0.0.1:8000 >/dev/null 2>&1; then
  echo "ERPNext does not look running on :8000"
  echo "In another terminal:"
  echo "  sudo service mariadb start"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo "  cd ~/frappe-bench && bench start"
  exit 1
fi

# Frappe routes by Host header (site name = qd.local)
echo "Starting ngrok → http://127.0.0.1:8000 (Host: qd.local)"
echo "Share the https://….ngrok-free.app URL with your manager."
echo "Login: Administrator / your admin password (or a test user)."
echo

exec ngrok http 8000 --host-header=qd.local
