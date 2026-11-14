"""
Database integrity checks and verification.
"""
import sqlite3
import os
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseIntegrityChecker:
    """Performs various integrity checks on the SQLite database."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def check_integrity(self) -> Dict[str, Any]:
        """Run full integrity check on the database."""
        if not os.path.exists(self.db_path):
            return {
                "healthy": False,
                "error": "Database file does not exist",
                "checks": {}
            }

        checks = {}
        all_passed = True

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # 1. SQLite integrity check
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            checks["sqlite_integrity"] = {
                "passed": result[0] == "ok",
                "result": result[0],
            }
            if result[0] != "ok":
                all_passed = False

            # 2. Foreign key check
            cursor = conn.execute("PRAGMA foreign_key_check")
            fk_violations = cursor.fetchall()
            checks["foreign_keys"] = {
                "passed": len(fk_violations) == 0,
                "violations": [dict(row) for row in fk_violations],
            }
            if fk_violations:
                all_passed = False

            # 3. Schema validation - check all expected tables exist
            expected_tables = [
                "campaigns", "campaign_evidence", "campaign_risk_findings",
                "campaign_eligibility", "campaign_field_history",
                "campaign_lifecycle_events", "campaign_merge_audit",
                "sources", "scan_history", "user_tracked", "user_notes",
                "settings", "risk_rules", "schema_migrations",
                "campaign_verification", "domain_verification",
                "campaign_risk_assessment", "campaign_claims",
                "campaign_events", "campaign_categories",
                "blockchains", "user_eligibility_progress",
                "user_notification_prefs", "risk_findings",
                "false_positive_review_queue",
            ]
            
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            missing_tables = [t for t in expected_tables if t not in existing_tables]
            extra_tables = [t for t in existing_tables if t not in expected_tables and not t.startswith("sqlite_")]
            
            checks["schema"] = {
                "passed": len(missing_tables) == 0,
                "missing_tables": missing_tables,
                "extra_tables": extra_tables,
                "total_tables": len(existing_tables),
            }
            if missing_tables:
                all_passed = False

            # 4. Check indexes
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            checks["indexes"] = {
                "count": len(indexes),
                "indexes": indexes,
            }

            # 5. Row count sanity checks
            table_counts = {}
            for table in ["campaigns", "sources", "scan_history", "campaign_evidence"]:
                if table in existing_tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
            
            checks["row_counts"] = table_counts

            # 6. Check for orphaned records
            orphan_checks = {}
            
            # Campaign evidence without campaign
            if "campaign_evidence" in existing_tables and "campaigns" in existing_tables:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM campaign_evidence ce
                    LEFT JOIN campaigns c ON ce.campaign_id = c.id
                    WHERE c.id IS NULL
                """)
                orphan_checks["orphaned_evidence"] = cursor.fetchone()[0]
            
            # Risk findings without campaign
            if "campaign_risk_findings" in existing_tables and "campaigns" in existing_tables:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM campaign_risk_findings crf
                    LEFT JOIN campaigns c ON crf.campaign_id = c.id
                    WHERE c.id IS NULL
                """)
                orphan_checks["orphaned_risk_findings"] = cursor.fetchone()[0]
            
            # Eligibility without campaign
            if "campaign_eligibility" in existing_tables and "campaigns" in existing_tables:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM campaign_eligibility ce
                    LEFT JOIN campaigns c ON ce.campaign_id = c.id
                    WHERE c.id IS NULL
                """)
                orphan_checks["orphaned_eligibility"] = cursor.fetchone()[0]

            total_orphans = sum(orphan_checks.values())
            checks["orphans"] = {
                "passed": total_orphans == 0,
                "details": orphan_checks,
                "total_orphans": total_orphans,
            }
            if total_orphans > 0:
                all_passed = False

            # 7. Check WAL mode
            cursor = conn.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            checks["wal_mode"] = {
                "passed": journal_mode.upper() == "WAL",
                "mode": journal_mode,
            }
            if journal_mode.upper() != "WAL":
                all_passed = False

            # 8. Check database size
            db_size = os.path.getsize(self.db_path)
            checks["database_size"] = {
                "bytes": db_size,
                "mb": round(db_size / (1024 * 1024), 2),
            }

            conn.close()

        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "checks": checks,
            }

        return {
            "healthy": all_passed,
            "checks": checks,
            "checked_at": datetime.utcnow().isoformat(),
        }

    def quick_health_check(self) -> bool:
        """Quick health check - just verify database is accessible and not corrupt."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.execute("PRAGMA quick_check")
            result = cursor.fetchone()
            conn.close()
            return result[0] == "ok"
        except Exception:
            return False

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed info about a specific table."""
        if not os.path.exists(self.db_path):
            return {"error": "Database not found"}

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Get table schema
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = [dict(row) for row in cursor.fetchall()]

            # Get row count
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            # Get indexes on this table
            cursor = conn.execute(f"PRAGMA index_list({table_name})")
            indexes = [dict(row) for row in cursor.fetchall()]

            # Get foreign keys
            cursor = conn.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = [dict(row) for row in cursor.fetchall()]

            conn.close()

            return {
                "table": table_name,
                "row_count": row_count,
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": foreign_keys,
            }
        except Exception as e:
            return {"error": str(e)}


def run_integrity_check(db_path: str) -> Dict[str, Any]:
    """Convenience function to run integrity check."""
    checker = DatabaseIntegrityChecker(db_path)
    return checker.check_integrity()


def quick_health_check(db_path: str) -> bool:
    """Quick health check."""
    checker = DatabaseIntegrityChecker(db_path)
    return checker.quick_health_check()