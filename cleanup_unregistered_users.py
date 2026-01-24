#!/usr/bin/env python3
"""Remove unregistered users from runtime data.

This script purges specified names from:
- data/user_ids.csv
- data/status_log.csv
- data/debug_log.csv (if present)
- data/attendance.xlsx (User Directory rows + monthly sheets)
- data/images/<name>/ and data/faces/<name>/ if such folders exist

It creates timestamped .bak backups before modifying any file.

Usage:
  python3 cleanup_unregistered_users.py --names John Mary --yes
  python3 cleanup_unregistered_users.py --names John Mary --dry-run
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


try:
    import openpyxl
except Exception:
    openpyxl = None


DATA_DIR = Path(__file__).resolve().parent / "data"


@dataclass(frozen=True)
class Change:
    path: Path
    description: str


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def backup_file(path: Path) -> Path:
    backup = path.with_suffix(path.suffix + f".bak-{_ts()}")
    shutil.copy2(path, backup)
    return backup


def normalize_name(name: str) -> str:
    return " ".join(name.strip().split())


def filter_csv_by_name(path: Path, names_to_remove: set[str], dry_run: bool) -> list[Change]:
    if not path.exists():
        return []

    # Read all rows (support inconsistent headers from older logs)
    with path.open("r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return []

    header = rows[0]
    name_col_idx = None
    for i, col in enumerate(header):
        if str(col).strip().lower() == "name":
            name_col_idx = i
            break

    # If no Name header, fall back to known layouts:
    # - status_log.csv: Timestamp,Name,... => Name is column 1
    # - debug_log.csv: time,name,status,... => name is column 1
    if name_col_idx is None:
        name_col_idx = 1

    kept = [header]
    removed_count = 0

    for row in rows[1:]:
        if not row:
            continue
        if len(row) <= name_col_idx:
            kept.append(row)
            continue
        row_name = normalize_name(str(row[name_col_idx]))
        if row_name in names_to_remove:
            removed_count += 1
            continue
        kept.append(row)

    if removed_count == 0:
        return []

    if dry_run:
        return [Change(path, f"Would remove {removed_count} rows for {sorted(names_to_remove)}")]

    backup_file(path)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(kept)

    return [Change(path, f"Removed {removed_count} rows for {sorted(names_to_remove)}")]


def cleanup_user_ids(path: Path, names_to_remove: set[str], dry_run: bool) -> list[Change]:
    if not path.exists():
        return []

    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return []

    kept = []
    removed = 0
    for row in rows:
        row_name = normalize_name(row.get("Name", ""))
        if row_name in names_to_remove:
            removed += 1
            continue
        kept.append(row)

    if removed == 0:
        return []

    if dry_run:
        return [Change(path, f"Would remove {removed} mappings")]

    backup_file(path)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "UserID"])
        writer.writeheader()
        writer.writerows(kept)

    return [Change(path, f"Removed {removed} mappings")]


def cleanup_excel(path: Path, names_to_remove: set[str], dry_run: bool) -> list[Change]:
    if openpyxl is None:
        return [Change(path, "openpyxl not available; skipped Excel cleanup")]
    if not path.exists():
        return []

    wb = openpyxl.load_workbook(path)
    changes: list[Change] = []

    # Remove monthly sheets like Name_Month_Year
    to_delete = []
    for sheet_name in wb.sheetnames:
        base = sheet_name.split("_")[0] if "_" in sheet_name else sheet_name
        if normalize_name(base) in names_to_remove:
            to_delete.append(sheet_name)

    if to_delete:
        if dry_run:
            changes.append(Change(path, f"Would remove sheets: {to_delete}"))
        else:
            backup_file(path)
            for sheet_name in to_delete:
                wb.remove(wb[sheet_name])
            changes.append(Change(path, f"Removed sheets: {to_delete}"))

    # Cleanup User Directory rows
    if "User Directory" in wb.sheetnames:
        ws = wb["User Directory"]
        # Typically: col B = Name
        rows_to_delete = []
        for r in range(1, ws.max_row + 1):
            val = ws.cell(r, 2).value
            if val is None:
                continue
            if normalize_name(str(val)) in names_to_remove:
                rows_to_delete.append(r)

        if rows_to_delete:
            if dry_run:
                changes.append(Change(path, f"Would delete User Directory rows: {rows_to_delete}"))
            else:
                if not any(c.path == path and c.description.startswith("Removed") for c in changes):
                    # Ensure we have a backup even if no sheets were deleted.
                    backup_file(path)

                for r in reversed(rows_to_delete):
                    ws.delete_rows(r, 1)

                # Re-number IDs in column A where possible
                next_id = 1
                for r in range(1, ws.max_row + 1):
                    a = ws.cell(r, 1).value
                    b = ws.cell(r, 2).value
                    if isinstance(a, int) and b:
                        ws.cell(r, 1).value = next_id
                        next_id += 1

                # Update total users value if present (label in col A, value in col C)
                for r in range(1, ws.max_row + 1):
                    if str(ws.cell(r, 1).value).strip() == "Total Users:":
                        ws.cell(r, 3).value = max(next_id - 1, 0)
                        break

                changes.append(Change(path, f"Deleted User Directory rows: {rows_to_delete}"))

    if dry_run:
        wb.close()
        return changes

    # Save only if we actually modified
    if any("Removed" in c.description or "Deleted" in c.description for c in changes):
        wb.save(path)
    wb.close()
    return changes


def cleanup_folders(names_to_remove: set[str], dry_run: bool) -> list[Change]:
    changes: list[Change] = []
    for folder in [DATA_DIR / "images", DATA_DIR / "faces"]:
        if not folder.exists():
            continue
        for name in names_to_remove:
            p = folder / name
            if p.exists() and p.is_dir():
                if dry_run:
                    changes.append(Change(p, "Would delete folder"))
                else:
                    shutil.rmtree(p)
                    changes.append(Change(p, "Deleted folder"))
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--names", nargs="+", required=True, help="Names to remove (exact match)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change")
    parser.add_argument("--yes", action="store_true", help="Actually apply changes")
    args = parser.parse_args()

    names = {normalize_name(n) for n in args.names}
    # Common typo safety: if user asked for Marry, also remove Mary if present
    if "Marry" in names:
        names.add("Mary")

    dry_run = args.dry_run or (not args.yes)

    changes: list[Change] = []

    changes += cleanup_user_ids(DATA_DIR / "user_ids.csv", names, dry_run)
    changes += filter_csv_by_name(DATA_DIR / "status_log.csv", names, dry_run)
    changes += filter_csv_by_name(DATA_DIR / "debug_log.csv", names, dry_run)
    changes += cleanup_excel(DATA_DIR / "attendance.xlsx", names, dry_run)
    changes += cleanup_folders(names, dry_run)

    if not changes:
        print("No matching unregistered users found in runtime data.")
        return 0

    mode = "DRY RUN" if dry_run else "APPLIED"
    print(f"\n[{mode}] Changes:")
    for ch in changes:
        print(f"- {ch.path}: {ch.description}")

    if dry_run:
        print("\nRe-run with --yes to apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
