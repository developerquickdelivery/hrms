#!/usr/bin/env bash
# Confirm the served portal stylesheet scopes login-only rules correctly.
set -uo pipefail

CSS_URL="http://127.0.0.1:8000/assets/qd_hrms/css/qd_login.css"
OUT=/tmp/qd_login_served.css

curl -s "${CSS_URL}" -o "${OUT}"
echo "bytes=$(wc -c < "${OUT}")"

echo "unscoped_body_blue=$(grep -cE '^[[:space:]]*background: #0c499c !important;' "${OUT}")   # want 0"
echo "scoped_auth_blue=$(grep -cF 'body[data-path="login"]' "${OUT}")   # want >=1"
echo "auth_class_hook=$(grep -cF 'body.qd-auth-page' "${OUT}")   # want >=1"
echo "sidebar_link_rules=$(grep -cF '.web-sidebar .sidebar-item a' "${OUT}")   # want >=1"
echo "portal_canvas=$(grep -cF -- '--qd-canvas: #f8fafc' "${OUT}")   # want 1"

echo "--- login-only title in js ---"
curl -s http://127.0.0.1:8000/assets/qd_hrms/js/qd_login.js -o /tmp/qd_login_served.js
echo "js_gated=$(grep -cF 'if (isAuthPage())' /tmp/qd_login_served.js)   # want 1"
