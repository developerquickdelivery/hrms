#!/usr/bin/env python3
"""Wrapper: run the on-prem biometric listener.

Copy scripts/qd_biometric_listener.example.json to qd_biometric_listener.json
and pass its path:

  python scripts/qd_biometric_listener.py qd_biometric_listener.json
"""

from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
LISTENER = ROOT / "qd_hrms_app" / "qd_hrms" / "integrations" / "listener.py"
if not LISTENER.exists():
	LISTENER = Path.home() / "frappe-bench/apps/qd_hrms/qd_hrms/integrations/listener.py"

runpy.run_path(str(LISTENER), run_name="__main__")
