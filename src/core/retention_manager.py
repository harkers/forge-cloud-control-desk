#!/usr/bin/env python3
"""GCCD Evidence Retention Manager

Automates cleanup of old evidence files per retention policy.

Policy:
- Evidence files: 90 days local, archive to Drive after 30 days
- Daily digests: 30 days
- Weekly reports: 1 year
- VM change log: indefinite (Sheets)

Usage:
    python3 src/core/retention_manager.py [--dry-run]
"""

import os
import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
EVIDENCE_DIR = project_root / "data" / "evidence"
ARCHIVE_DIR = project_root / "data" / "archive"

# Retention policy (days)
POLICY = {
    "vm_operations": 90,
    "inspections": 90,
    "service_health": 30,
    "notifications": 7,
    "reports/daily": 30,
    "reports/weekly": 365,
    "mail-events": 30,
}


def get_file_age(filepath: Path) -> int:
    """Get file age in days."""
    mtime = filepath.stat().st_mtime
    return (datetime.now() - datetime.fromtimestamp(mtime)).days


def should_archive(category: str, age_days: int) -> bool:
    """Check if file should be archived (older than half retention)."""
    retention = POLICY.get(category, 90)
    return age_days > retention // 3  # Archive after 1/3 of retention period


def should_delete(category: str, age_days: int) -> bool:
    """Check if file should be deleted (past retention)."""
    retention = POLICY.get(category, 90)
    return age_days > retention


def process_category(category_dir: Path, dry_run: bool = False) -> dict:
    """Process all files in a category directory."""
    stats = {"archived": 0, "deleted": 0, "kept": 0, "errors": []}
    
    if not category_dir.exists():
        return stats
    
    category = category_dir.name
    
    for filepath in category_dir.iterdir():
        if not filepath.is_file():
            continue
        
        try:
            age_days = get_file_age(filepath)
            
            if should_delete(category, age_days):
                if dry_run:
                    print(f"[DRY-RUN] Would delete: {filepath.name} ({age_days} days old)")
                else:
                    filepath.unlink()
                    print(f"Deleted: {filepath.name} ({age_days} days old)")
                stats["deleted"] += 1
                
            elif should_archive(category, age_days):
                # Archive to Drive (placeholder — would use Drive API)
                if dry_run:
                    print(f"[DRY-RUN] Would archive: {filepath.name} ({age_days} days old)")
                else:
                    # TODO: Upload to Drive, then delete local
                    print(f"Archive pending: {filepath.name} ({age_days} days old)")
                stats["archived"] += 1
                
            else:
                stats["kept"] += 1
                
        except Exception as e:
            stats["errors"].append(f"{filepath.name}: {e}")
    
    return stats


def main():
    """Main entry point."""
    dry_run = "--dry-run" in sys.argv
    
    print("🧹 GCCD Evidence Retention Manager")
    print(f"   Evidence dir: {EVIDENCE_DIR}")
    print(f"   Mode: {'DRY-RUN' if dry_run else 'LIVE'}")
    print("")
    
    if not EVIDENCE_DIR.exists():
        print("No evidence directory found. Nothing to do.")
        return
    
    total_stats = {"archived": 0, "deleted": 0, "kept": 0, "errors": []}
    
    # Process each category
    for category in POLICY.keys():
        category_dir = EVIDENCE_DIR / category.replace("/", "-")
        if category_dir.exists():
            print(f"\n📁 Processing {category}...")
            stats = process_category(category_dir, dry_run)
            
            total_stats["archived"] += stats["archived"]
            total_stats["deleted"] += stats["deleted"]
            total_stats["kept"] += stats["kept"]
            total_stats["errors"].extend(stats["errors"])
            
            print(f"   Archived: {stats['archived']}")
            print(f"   Deleted: {stats['deleted']}")
            print(f"   Kept: {stats['kept']}")
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Total archived: {total_stats['archived']}")
    print(f"Total deleted: {total_stats['deleted']}")
    print(f"Total kept: {total_stats['kept']}")
    
    if total_stats['errors']:
        print(f"\n⚠️  Errors: {len(total_stats['errors'])}")
        for error in total_stats['errors'][:5]:
            print(f"   - {error}")
    
    print("")
    print(f"Retention run completed at {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
