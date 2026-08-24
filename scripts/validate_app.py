#!/usr/bin/env python3
"""Dependency-free source and Frappe metadata checks for CI and releases."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "qd_hrms_app"
PACKAGE_ROOT = APP_ROOT / "qd_hrms"


def main() -> int:
	errors: list[str] = []
	python_files = sorted(APP_ROOT.rglob("*.py"))
	json_files = sorted(APP_ROOT.rglob("*.json"))

	for path in python_files:
		try:
			ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
		except (OSError, SyntaxError, UnicodeError) as exc:
			errors.append(f"{path.relative_to(ROOT)}: {exc}")

	for path in json_files:
		try:
			payload = json.loads(path.read_text(encoding="utf-8"))
		except (OSError, ValueError, UnicodeError) as exc:
			errors.append(f"{path.relative_to(ROOT)}: {exc}")
			continue
		if path.parent.parent.name == "doctype" and payload.get("doctype") == "DocType":
			_validate_doctype(path, payload, errors)
		if path.parent.parent.name == "report" and payload.get("doctype") == "Report":
			_validate_report(path, payload, errors)

	if not (APP_ROOT / "pyproject.toml").is_file():
		errors.append("qd_hrms_app/pyproject.toml is missing")
	if not (PACKAGE_ROOT / "hooks.py").is_file():
		errors.append("qd_hrms_app/qd_hrms/hooks.py is missing")

	print(
		f"Validated {len(python_files)} Python files and {len(json_files)} JSON files; "
		f"{len(errors)} error(s)."
	)
	for error in errors:
		print(f"ERROR: {error}")
	return 1 if errors else 0


def _validate_doctype(path: Path, payload: dict, errors: list[str]) -> None:
	name = payload.get("name")
	if not name:
		errors.append(f"{path.relative_to(ROOT)}: DocType name is missing")
	if payload.get("module") != "QD HRMS":
		errors.append(f"{path.relative_to(ROOT)}: module must be QD HRMS")
	fieldnames = [field.get("fieldname") for field in payload.get("fields", [])]
	duplicates = sorted({fieldname for fieldname in fieldnames if fieldnames.count(fieldname) > 1})
	if duplicates:
		errors.append(
			f"{path.relative_to(ROOT)}: duplicate fieldnames: {', '.join(duplicates)}"
		)
	controller = path.with_suffix(".py")
	if not controller.is_file():
		errors.append(f"{controller.relative_to(ROOT)}: controller is missing")


def _validate_report(path: Path, payload: dict, errors: list[str]) -> None:
	if payload.get("report_type") != "Script Report":
		return
	for suffix in (".py", ".js"):
		companion = path.with_suffix(suffix)
		if not companion.is_file():
			errors.append(f"{companion.relative_to(ROOT)}: Script Report companion is missing")


if __name__ == "__main__":
	sys.exit(main())
