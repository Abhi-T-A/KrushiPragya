"""baseline existing schema

Revision ID: 917bd8d97856
Revises: 
Create Date: 2026-09-23

Baseline represents the pre-existing database schema in Supabase:
- villages
- weather_seed
- advisory_rules
- disease_risk_kb
- models
- model_metrics
- datasets
- dataset_images
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '917bd8d97856'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Baseline placeholder: tables already exist in remote Supabase PostgreSQL
    pass


def downgrade() -> None:
    # Baseline placeholder: non-destructive
    pass
