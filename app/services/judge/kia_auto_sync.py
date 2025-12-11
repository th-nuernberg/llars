"""
KIA Auto-Sync Service - Automatisches Laden von KIA-Daten beim App-Start.

Prüft beim Start ob pillar_threads leer ist und synchronisiert automatisch
alle verfügbaren Säulen aus dem GitLab Repository.
"""

import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

_sync_thread: Optional[threading.Thread] = None
_sync_started = False


def _run_auto_sync(app):
    """
    Background thread that syncs KIA data if no threads exist.

    Runs once at startup with a small delay to let the app fully initialize.
    """
    # Wait for app to fully start
    time.sleep(10)

    with app.app_context():
        from db.tables import PillarThread
        from services.judge.kia_sync_service import get_kia_sync_service, PILLAR_CONFIG

        try:
            # Check if we have any pillar threads
            thread_count = PillarThread.query.count()

            if thread_count > 0:
                logger.info(f"[KIA-AutoSync] {thread_count} pillar threads already exist, skipping auto-sync")
                return

            logger.info("[KIA-AutoSync] No pillar threads found, starting automatic sync...")

            # Get sync service
            sync_service = get_kia_sync_service()

            # Check if we can connect to GitLab
            project_id = sync_service._get_project_id()
            if not project_id:
                logger.warning("[KIA-AutoSync] Cannot connect to GitLab, skipping auto-sync")
                return

            logger.info(f"[KIA-AutoSync] Connected to GitLab (project ID: {project_id})")

            # Check availability first
            availability = sync_service.check_pillar_availability()

            available_pillars = [
                num for num, status in availability.items()
                if status.status.value == 'available'
            ]

            if not available_pillars:
                logger.warning("[KIA-AutoSync] No pillars with data available in GitLab")
                return

            logger.info(f"[KIA-AutoSync] Found {len(available_pillars)} pillars with data: {available_pillars}")

            # Sync each available pillar
            total_created = 0
            for pillar_num in available_pillars:
                logger.info(f"[KIA-AutoSync] Syncing Säule {pillar_num}...")
                result = sync_service.sync_pillar(pillar_num, force=False)

                if result.success:
                    logger.info(
                        f"[KIA-AutoSync] Säule {pillar_num}: "
                        f"{result.threads_created} created, {result.threads_skipped} skipped"
                    )
                    total_created += result.threads_created
                else:
                    logger.warning(
                        f"[KIA-AutoSync] Säule {pillar_num} failed: {result.errors[:3]}"
                    )

            logger.info(f"[KIA-AutoSync] Auto-sync complete: {total_created} threads created")

        except Exception as e:
            logger.error(f"[KIA-AutoSync] Error during auto-sync: {e}")


def start_kia_auto_sync(app):
    """
    Start the KIA auto-sync background thread.

    Called once at app startup. Checks if pillar_threads is empty
    and automatically syncs KIA data from GitLab if needed.
    """
    global _sync_thread, _sync_started

    if _sync_started:
        logger.debug("[KIA-AutoSync] Already started, skipping")
        return

    _sync_started = True

    logger.info("[KIA-AutoSync] Starting auto-sync check...")

    _sync_thread = threading.Thread(
        target=_run_auto_sync,
        args=(app,),
        daemon=True,
        name="KIA-AutoSync"
    )
    _sync_thread.start()
