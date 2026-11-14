"""
Scheduled jobs for Global Airdrop Hunter.
Handles periodic tasks like lifecycle detection, cleanup, etc.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.database.repositories.campaign import campaign_repository
from backend.core.discovery import discovery_service

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


async def run_lifecycle_detection():
    """Run lifecycle change detection for all campaigns."""
    logger.info("Starting lifecycle detection job")
    try:
        changes = campaign_repository.detect_lifecycle_changes()
        logger.info(f"Lifecycle detection completed: {changes}")
        return changes
    except Exception as e:
        logger.error(f"Lifecycle detection failed: {e}")
        raise


async def run_evidence_refresh():
    """Refresh evidence for campaigns (fetch content, snippets, content hashes)."""
    logger.info("Starting evidence refresh job")
    # This would fetch content from evidence URLs and store snippets/hashes
    # For now, just log
    logger.info("Evidence refresh completed")
    return {"refreshed": 0}


async def run_scan_scheduler():
    """Run scheduled discovery scans."""
    logger.info("Starting scheduled scan")
    try:
        from backend.core.models import ScanRequest
        request = ScanRequest(sources=None)  # Scan all enabled sources
        result = await discovery_service.run_scan(request)
        logger.info(f"Scheduled scan completed: {result.campaigns_found} campaigns found")
        return result
    except Exception as e:
        logger.error(f"Scheduled scan failed: {e}")
        raise


def start_scheduler():
    """Start the APScheduler with configured jobs."""
    global _scheduler
    
    if _scheduler and _scheduler.running:
        logger.warning("Scheduler already running")
        return _scheduler
    
    _scheduler = AsyncIOScheduler()
    
    # Lifecycle detection - every 6 hours
    _scheduler.add_job(
        run_lifecycle_detection,
        IntervalTrigger(hours=6),
        id='lifecycle_detection',
        name='Campaign Lifecycle Detection',
        max_instances=1,
        coalesce=True,
    )
    
    # Evidence refresh - daily
    _scheduler.add_job(
        run_evidence_refresh,
        IntervalTrigger(hours=24),
        id='evidence_refresh',
        name='Evidence Content Refresh',
        max_instances=1,
        coalesce=True,
    )
    
    # Scheduled scans - every 4 hours (configurable)
    _scheduler.add_job(
        run_scan_scheduler,
        IntervalTrigger(hours=4),
        id='scheduled_scan',
        name='Scheduled Discovery Scan',
        max_instances=1,
        coalesce=True,
    )
    
    _scheduler.start()
    logger.info("Scheduler started with jobs: lifecycle_detection, evidence_refresh, scheduled_scan")
    
    return _scheduler


def stop_scheduler():
    """Stop the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        logger.info("Scheduler stopped")


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """Get the scheduler instance."""
    return _scheduler


async def run_all_maintenance():
    """Run all maintenance tasks once (for manual testing)."""
    results = {}
    results['lifecycle'] = await run_lifecycle_detection()
    results['evidence'] = await run_evidence_refresh()
    results['scan'] = await run_scan_scheduler()
    return results