from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from typing import Optional
from uuid import UUID
import shutil
import os
import hashlib
import json
from datetime import datetime

from backend.database.connection import get_db
from backend.config import get_settings
from backend.core.models import BackupResponse

router = APIRouter()


def calculate_sha256(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def create_backup_manifest(backup_path: str, db_path: str) -> dict:
    """Create a manifest for the backup with metadata and SHA256."""
    stat = os.stat(backup_path)
    db_stat = os.stat(db_path) if os.path.exists(db_path) else None
    
    manifest = {
        "backup_file": os.path.basename(backup_path),
        "backup_sha256": calculate_sha256(backup_path),
        "backup_size_bytes": stat.st_size,
        "backup_created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "source_db_path": db_path,
        "source_db_size_bytes": db_stat.st_size if db_stat else None,
        "source_db_modified_at": datetime.fromtimestamp(db_stat.st_mtime).isoformat() if db_stat else None,
        "manifest_version": 1,
        "created_at": datetime.utcnow().isoformat(),
    }
    return manifest


def verify_backup_manifest(backup_path: str, manifest_path: str) -> tuple[bool, Optional[str]]:
    """Verify backup against its manifest."""
    if not os.path.exists(manifest_path):
        return False, "Manifest file not found"
    
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        return False, f"Invalid manifest: {e}"
    
    # Verify SHA256
    actual_sha256 = calculate_sha256(backup_path)
    if actual_sha256 != manifest.get("backup_sha256"):
        return False, f"SHA256 mismatch: expected {manifest.get('backup_sha256')}, got {actual_sha256}"
    
    # Verify size
    actual_size = os.path.getsize(backup_path)
    if actual_size != manifest.get("backup_size_bytes"):
        return False, f"Size mismatch: expected {manifest.get('backup_size_bytes')}, got {actual_size}"
    
    return True, None


@router.post("/backup", response_model=BackupResponse, status_code=status.HTTP_201_CREATED)
async def create_backup(
    verify: bool = Query(True, description="Verify backup integrity after creation")
):
    """Create a timestamped backup of the SQLite database with SHA256 manifest."""
    settings = get_settings()
    db_path = settings.database_path
    
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail={"code": "NO_DATABASE", "message": "Database file not found"})
    
    # Create backup directory
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create timestamped backup filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"app_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        # Verify backup integrity if requested
        integrity_verified = False
        if verify:
            import sqlite3
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            integrity_verified = (result[0] == "ok")
            conn.close()
            
            if not integrity_verified:
                os.remove(backup_path)
                raise HTTPException(status_code=500, detail={"code": "BACKUP_CORRUPT", "message": "Backup integrity check failed"})
        
        # Create manifest with SHA256
        manifest = create_backup_manifest(backup_path, db_path)
        manifest_path = backup_path + ".manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        # Get backup size
        size_bytes = os.path.getsize(backup_path)
        
        return BackupResponse(
            backup_path=backup_path,
            size_bytes=size_bytes,
            integrity_verified=integrity_verified
        )
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on failure
        if os.path.exists(backup_path):
            os.remove(backup_path)
        manifest_path = backup_path + ".manifest.json"
        if os.path.exists(manifest_path):
            os.remove(manifest_path)
        raise HTTPException(status_code=500, detail={"code": "BACKUP_FAILED", "message": str(e)})


@router.get("/backups", response_model=list)
async def list_backups():
    """List available backups with manifest info."""
    settings = get_settings()
    db_path = settings.database_path
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    
    if not os.path.exists(backup_dir):
        return []
    
    backups = []
    for filename in sorted(os.listdir(backup_dir), reverse=True):
        if filename.endswith(".db") and filename.startswith("app_"):
            filepath = os.path.join(backup_dir, filename)
            stat = os.stat(filepath)
            
            # Check for manifest
            manifest_path = filepath + ".manifest.json"
            manifest = None
            manifest_verified = False
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r") as f:
                        manifest = json.load(f)
                    manifest_verified, _ = verify_backup_manifest(filepath, manifest_path)
                except Exception:
                    pass
            
            backups.append({
                "filename": filename,
                "path": filepath,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "manifest": manifest,
                "manifest_verified": manifest_verified,
            })
    
    return backups


@router.post("/restore", status_code=status.HTTP_200_OK)
async def restore_backup(
    filename: str = Query(..., description="Backup filename to restore"),
    verify_manifest: bool = Query(True, description="Verify manifest SHA256 before restore"),
):
    """Restore database from a backup file with manifest verification."""
    settings = get_settings()
    db_path = settings.database_path
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    backup_path = os.path.join(backup_dir, filename)
    
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail={"code": "BACKUP_NOT_FOUND", "message": "Backup file not found"})
    
    # Verify manifest if requested
    if verify_manifest:
        manifest_path = backup_path + ".manifest.json"
        verified, error = verify_backup_manifest(backup_path, manifest_path)
        if not verified:
            raise HTTPException(status_code=400, detail={"code": "MANIFEST_VERIFICATION_FAILED", "message": f"Manifest verification failed: {error}"})
    
    # Verify backup integrity before restore
    import sqlite3
    conn = sqlite3.connect(backup_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check")
    result = cursor.fetchone()
    conn.close()
    
    if result[0] != "ok":
        raise HTTPException(status_code=400, detail={"code": "BACKUP_CORRUPT", "message": "Backup integrity check failed"})
    
    # Create a backup of current database before restore
    if os.path.exists(db_path):
        pre_restore_backup = f"{db_path}.pre_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, pre_restore_backup)
    
    try:
        # Restore the database
        shutil.copy2(backup_path, db_path)
        return {"message": "Database restored successfully", "restored_from": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "RESTORE_FAILED", "message": str(e)})


@router.get("/verify/{filename}", status_code=status.HTTP_200_OK)
async def verify_backup(filename: str):
    """Verify a backup file's integrity and manifest."""
    settings = get_settings()
    db_path = settings.database_path
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    backup_path = os.path.join(backup_dir, filename)
    
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail={"code": "BACKUP_NOT_FOUND", "message": "Backup file not found"})
    
    results = {
        "filename": filename,
        "integrity_check": False,
        "manifest_check": False,
        "manifest_verified": False,
        "errors": [],
    }
    
    # SQLite integrity check
    try:
        import sqlite3
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        results["integrity_check"] = (result[0] == "ok")
        if result[0] != "ok":
            results["errors"].append(f"Integrity check failed: {result[0]}")
    except Exception as e:
        results["errors"].append(f"Integrity check error: {e}")
    
    # Manifest verification
    manifest_path = backup_path + ".manifest.json"
    if os.path.exists(manifest_path):
        results["manifest_check"] = True
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            results["manifest"] = manifest
            
            verified, error = verify_backup_manifest(backup_path, manifest_path)
            results["manifest_verified"] = verified
            if not verified:
                results["errors"].append(f"Manifest verification failed: {error}")
        except Exception as e:
            results["errors"].append(f"Manifest error: {e}")
    else:
        results["errors"].append("No manifest file found")
    
    return results