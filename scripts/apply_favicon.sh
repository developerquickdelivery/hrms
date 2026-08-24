#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
BENCH="${HOME}/frappe-bench"
SRC="/mnt/c/anw/work/QD-HRMS/qd_hrms_app"
DEST="${BENCH}/apps/qd_hrms"
IMG="${DEST}/qd_hrms/public/images"
cd "${BENCH}"

mkdir -p "${DEST}/qd_hrms/public/js" "${DEST}/qd_hrms/setup"
cp -a "${SRC}/qd_hrms/hooks.py" "${DEST}/qd_hrms/hooks.py"
cp -a "${SRC}/qd_hrms/setup/branding.py" "${DEST}/qd_hrms/setup/branding.py"
cp -a "${SRC}/qd_hrms/public/js/qd_hrms.js" "${DEST}/qd_hrms/public/js/qd_hrms.js"
cp -a "${SRC}/qd_hrms/public/js/qd_login.js" "${DEST}/qd_hrms/public/js/qd_login.js"

# Build a rounded-square favicon from the official runner logo (not the crafted QD mark).
"${BENCH}/env/bin/python" - <<'PY'
from pathlib import Path
from PIL import Image, ImageDraw

src_path = Path.home() / "frappe-bench/apps/qd_hrms/qd_hrms/public/images/qd-logo.png"
out_path = src_path.with_name("qd-favicon.png")
win_path = Path("/mnt/c/anw/work/QD-HRMS/qd_hrms_app/qd_hrms/public/images/qd-favicon.png")

img = Image.open(src_path).convert("RGBA")
size = 128
img = img.resize((size, size), Image.Resampling.LANCZOS)

mask = Image.new("L", (size, size), 0)
draw = ImageDraw.Draw(mask)
radius = int(size * 0.22)
draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)

out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
out.paste(img, (0, 0))
out.putalpha(mask)
out.save(out_path, "PNG", optimize=True)
win_path.parent.mkdir(parents=True, exist_ok=True)
out.save(win_path, "PNG", optimize=True)
print("wrote", out_path, out.size, out_path.stat().st_size, "bytes")
PY

rm -f "${IMG}/qd-favicon.svg" "${SRC}/qd_hrms/public/images/qd-favicon.svg"

bench --site qd.local execute qd_hrms.setup.branding.run
bench --site qd.local clear-cache
echo DONE
