import sqlite3
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from backend.database.connection import get_db
from backend.core.models import (
    Source, SourceCreate, SourceUpdate, SourceType, SourceStatus
)


class SourceRepository:
    def __init__(self):
        pass

    def _row_to_source(self, row: sqlite3.Row) -> Source:
        return Source(
            id=row["id"],
            name=row["name"],
            type=SourceType(row["type"]),
            base_url=row["base_url"],
            config=json.loads(row["config"]) if row["config"] else {},
            rate_limit=row["rate_limit"],
            timeout=row["timeout"],
            status=SourceStatus(row["status"]),
            enabled=bool(row["enabled"]),
            last_health_check=datetime.fromisoformat(row["last_health_check"]) if row["last_health_check"] else None,
            last_scan=datetime.fromisoformat(row["last_scan"]) if row["last_scan"] else None,
            consecutive_failures=row["consecutive_failures"],
            total_scans=row["total_scans"],
            total_records=row["total_records"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def create(self, source: SourceCreate) -> Source:
        with get_db() as db:
            now = datetime.utcnow().isoformat()
            source_id = str(uuid.uuid4())

            db.execute("""
                INSERT INTO sources (id, name, type, base_url, config, rate_limit, timeout, status, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_id, source.name, source.type.value, str(source.base_url),
                json.dumps(source.config), source.rate_limit, source.timeout,
                SourceStatus.ENABLED.value, 1, now, now
            ))

            return self.get_by_id(source_id)

    def get_by_id(self, source_id: str) -> Optional[Source]:
        with get_db() as db:
            row = db.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
            if not row:
                return None
            return self._row_to_source(row)

    def get_by_name(self, name: str) -> Optional[Source]:
        with get_db() as db:
            row = db.execute("SELECT * FROM sources WHERE name = ?", (name,)).fetchone()
            if not row:
                return None
            return self._row_to_source(row)

    def list(self, enabled_only: bool = False) -> List[Source]:
        with get_db() as db:
            if enabled_only:
                rows = db.execute("SELECT * FROM sources WHERE enabled = 1 ORDER BY name").fetchall()
            else:
                rows = db.execute("SELECT * FROM sources ORDER BY name").fetchall()
            return [self._row_to_source(row) for row in rows]

    def update(self, source_id: str, update: SourceUpdate) -> Optional[Source]:
        with get_db() as db:
            existing = db.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
            if not existing:
                return None

            now = datetime.utcnow().isoformat()
            updates = []
            params = []

            fields = {
                "name": update.name,
                "base_url": str(update.base_url) if update.base_url else None,
                "config": json.dumps(update.config) if update.config is not None else None,
                "rate_limit": update.rate_limit,
                "timeout": update.timeout,
                "status": update.status.value if update.status else None,
                "enabled": 1 if update.enabled else 0 if update.enabled is not None else None,
            }

            for field, value in fields.items():
                if value is not None:
                    updates.append(f"{field} = ?")
                    params.append(value)

            if updates:
                updates.append("updated_at = ?")
                params.append(now)
                params.append(source_id)
                db.execute(f"UPDATE sources SET {', '.join(updates)} WHERE id = ?", params)

            return self.get_by_id(source_id)

    def delete(self, source_id: str) -> bool:
        with get_db() as db:
            cursor = db.execute("DELETE FROM sources WHERE id = ?", (source_id,))
            return cursor.rowcount > 0

    def update_health_check(self, source_id: str, success: bool) -> None:
        with get_db() as db:
            now = datetime.utcnow().isoformat()
            if success:
                db.execute("""
                    UPDATE sources SET last_health_check = ?, consecutive_failures = 0 WHERE id = ?
                """, (now, source_id))
            else:
                db.execute("""
                    UPDATE sources SET last_health_check = ?, consecutive_failures = consecutive_failures + 1 WHERE id = ?
                """, (now, source_id))

    def update_scan_stats(self, source_id: str, records_found: int) -> None:
        with get_db() as db:
            now = datetime.utcnow().isoformat()
            db.execute("""
                UPDATE sources SET last_scan = ?, total_scans = total_scans + 1, total_records = total_records + ? WHERE id = ?
            """, (now, records_found, source_id))

    def get_enabled_sources(self) -> List[Source]:
        return self.list(enabled_only=True)


source_repository = SourceRepository()