"""Initial schema migration for AGNI-NETRA Phase 1

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-28 11:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schema tables are created via Base.metadata.create_all() or direct DDL
    pass


def downgrade() -> None:
    pass
