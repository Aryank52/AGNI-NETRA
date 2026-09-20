"""
AGNI-NETRA — Production Satellite FIRMS Ingestion Loop Worker Daemon
Continuously runs scheduled ingestion cycles for NASA FIRMS VIIRS/MODIS thermal telemetry.
Suitable for execution in Render worker instances or containerized daemons.
"""
import os
import sys
import time
import signal
import logging
import argparse
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [FIRMS-WORKER] %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("firms_ingest_loop")

POLL_INTERVAL_SECONDS = int(os.getenv("FIRMS_POLL_INTERVAL_SECONDS", "900"))  # Default: 15 mins
_SHUTDOWN_REQUESTED = False


def signal_handler(signum, frame):
    global _SHUTDOWN_REQUESTED
    logger.info(f"Signal {signum} received. Initiating graceful shutdown of FIRMS daemon...")
    _SHUTDOWN_REQUESTED = True


def run_loop(single_run: bool = False):
    global _SHUTDOWN_REQUESTED
    logger.info("Initializing AGNI-NETRA NASA FIRMS Ingestion Daemon (WP3 Hardened)...")
    
    # Register signal handlers where supported
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except Exception:
        pass

    from backend.app.tasks.maintenance_tasks import firms_ingestion_job
    logger.info(f"Worker initialized. Scheduled polling interval: {POLL_INTERVAL_SECONDS}s. Single-run: {single_run}")
    
    cycle_num = 1
    consecutive_errors = 0

    while not _SHUTDOWN_REQUESTED:
        try:
            logger.info(f"[Cycle {cycle_num}] Triggering NASA FIRMS telemetry ingestion...")
            result = firms_ingestion_job()
            logger.info(f"[Cycle {cycle_num}] Ingestion result: {result}")
            consecutive_errors = 0
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"[Cycle {cycle_num}] Ingestion error (consecutive: {consecutive_errors}): {e}", exc_info=True)
            
        if single_run or _SHUTDOWN_REQUESTED:
            logger.info("FIRMS ingestion worker completed target run or received shutdown.")
            break

        cycle_num += 1
        # If error occurred, apply dynamic error backoff up to interval
        sleep_duration = min(POLL_INTERVAL_SECONDS, max(10, 10 * (2 ** (consecutive_errors - 1)))) if consecutive_errors > 0 else POLL_INTERVAL_SECONDS
        logger.info(f"Sleeping for {sleep_duration}s until next ingestion cycle...")
        
        # Incremental sleep to respond promptly to shutdown signals
        slept = 0
        while slept < sleep_duration and not _SHUTDOWN_REQUESTED:
            time.sleep(1)
            slept += 1

    logger.info("AGNI-NETRA FIRMS daemon exited cleanly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGNI-NETRA FIRMS Ingestion Daemon")
    parser.add_argument("--once", action="store_true", help="Execute a single ingestion cycle and exit")
    args = parser.parse_args()
    run_loop(single_run=args.once)

