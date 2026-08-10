#!/usr/bin/env bash
set -euo pipefail

# Install ngrok binary into ~/.local/bin (no snap needed)
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/ngrok"
cd /tmp

ARCH=$(uname -m)
case "$ARCH" in
  x86_64) NGROK_ZIP=ngrok-v3-stable-linux-amd64.tgz ;;
  aarch64|arm64) NGROK_ZIP=ngrok-v3-stable-linux-arm64.tgz ;;
  *) echo "Unsupported arch: $ARCH"; exit 1 ;;
esac

echo "Downloading ngrok..."
curl -fsSL -o "$NGROK_ZIP" "https://bin.equinox.io/c/bNyj1mQVY4c/${NGROK_ZIP}"
tar -xzf "$NGROK_ZIP"
mv -f ngrok "$HOME/.local/bin/ngrok"
chmod +x "$HOME/.local/bin/ngrok"
rm -f "$NGROK_ZIP"

export PATH="$HOME/.local/bin:$PATH"
echo "Installed: $(command -v ngrok)"
ngrok version
