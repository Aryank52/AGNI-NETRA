"""Complete schema, telemetry, mission tasks and historical thermal archive for AGNI-NETRA

Revision ID: 002_complete_schema_and_telemetry
Revises: 001_initial_schema
Create Date: 2026-08-30 01:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.core.database import Base
import backend.app.models.domain  # noqa: F401

revision: str = '002_complete_schema'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    pass
