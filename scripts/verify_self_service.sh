#!/usr/bin/env bash
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
cd "${HOME}/frappe-bench"

bench --site qd.local mariadb <<'SQL'
SELECT name, public, icon, module FROM tabWorkspace WHERE name='My HR';
SELECT label, link_to FROM `tabWorkspace Shortcut` WHERE parent='My HR' ORDER BY idx;
SELECT document_type, `read`, `write`, `create`, submit
FROM `tabUser Document Type`
WHERE parent='Employee Self Service'
  AND document_type IN (
    'QD Employee Document',
    'Asset',
    'Training Event',
    'Attendance',
    'QD Policy Acknowledgement',
    'Salary Slip',
    'Leave Application'
  )
ORDER BY document_type;
SQL

echo "DocType exists:"
bench --site qd.local mariadb -e "SELECT name FROM tabDocType WHERE name='QD Employee Document';"
