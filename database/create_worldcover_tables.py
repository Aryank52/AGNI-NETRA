"""
AGNI-NETRA — Phase 3D: ESA WorldCover 10m PostGIS Tile Index & Table Creation
Creates:
- lulc_raster_tiles (Indexed with PostGIS GiST bounding boxes)
"""

import os
import sys
import logging
from sqlalchemy import text

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.database import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WorldCoverSchema")


def create_worldcover_tables():
    logger.info("Initializing ESA WorldCover 10m Raster Tile Registry Schema...")
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lulc_raster_tiles (
                id VARCHAR(64) PRIMARY KEY,
                source_id VARCHAR(64) REFERENCES lulc_sources(id) ON DELETE CASCADE,
                tile_id VARCHAR(100) UNIQUE NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                geom GEOMETRY(Polygon, 4326) NOT NULL,
                min_lat FLOAT NOT NULL,
                max_lat FLOAT NOT NULL,
                min_lon FLOAT NOT NULL,
                max_lon FLOAT NOT NULL,
                srid INTEGER DEFAULT 4326,
                resolution_m FLOAT DEFAULT 10.0,
                reference_year INTEGER DEFAULT 2021,
                checksum VARCHAR(64),
                status VARCHAR(50) DEFAULT 'ACTIVE',
                metadata_info JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_lulc_raster_tiles_geom ON lulc_raster_tiles USING GIST (geom);
            CREATE INDEX IF NOT EXISTS idx_lulc_raster_tiles_tile_id ON lulc_raster_tiles(tile_id);
            CREATE INDEX IF NOT EXISTS idx_lulc_raster_tiles_source_id ON lulc_raster_tiles(source_id);
        """))
        logger.info("Created table lulc_raster_tiles with GiST spatial index.")


if __name__ == "__main__":
    create_worldcover_tables()
