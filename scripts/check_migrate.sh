#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
ps -u qd -o pid,etime,cmd 2>/dev/null | grep -E 'bench|frappe|yarn|esbuild' | grep -v grep || true
echo '---'
tail -n 20 /mnt/c/Users/User/.cursor/projects/c-anw-work-QD-HRMS/terminals/770221.txt 2>/dev/null || true
