"""
AGNI-NETRA — Production Satellite FIRMS Ingestion Loop Worker Daemon
Continuously runs scheduled ingestion cycles for NASA FIRMS VIIRS/MODIS thermal telemetry.
Suitable for execution in Render worker instances or containerized daemons.
"""
import os
import sys
import time
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [FIRMS-WORKER] %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("firms_ingest_loop")

POLL_INTERVAL_SECONDS = int(os.getenv("FIRMS_POLL_INTERVAL_SECONDS", "900"))  # Default: 15 mins

def run_loop():
    logger.info("Initializing AGNI-NETRA NASA FIRMS Ingestion Daemon...")
    from backend.app.tasks.maintenance_tasks import firms_ingestion_job
    logger.info(f"Worker initialized. Scheduled polling interval: {POLL_INTERVAL_SECONDS}s.")
    
    cycle_num = 1
    while True:
        try:
            logger.info(f"[Cycle {cycle_num}] Triggering NASA FIRMS telemetry ingestion...")
            result = firms_ingestion_job()
            logger.info(f"[Cycle {cycle_num}] Ingestion result: {result}")
        except Exception as e:
            logger.error(f"[Cycle {cycle_num}] Ingestion error: {e}", exc_info=True)
            
        cycle_num += 1
        logger.info(f"Sleeping for {POLL_INTERVAL_SECONDS}s until next ingestion cycle...")
        try:
            time.sleep(POLL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            logger.info("FIRMS ingestion daemon received interrupt signal. Graceful shutdown.")
            break

if __name__ == "__main__":
    run_loop()
