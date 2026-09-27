"""add_expert_verification_request_fields

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-26 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Additive and non-destructive columns for expert review request & demo payment
    op.execute(
        """
        ALTER TABLE expert_verification_requests 
        ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'SUCCESS',
        ADD COLUMN IF NOT EXISTS payment_mode VARCHAR(50) DEFAULT 'DEMO',
        ADD COLUMN IF NOT EXISTS payment_amount NUMERIC(10, 2) DEFAULT 49.00,
        ADD COLUMN IF NOT EXISTS crop VARCHAR(100),
        ADD COLUMN IF NOT EXISTS diagnosis VARCHAR(255),
        ADD COLUMN IF NOT EXISTS ai_confidence FLOAT;
        """
    )


def downgrade() -> None:
    # Non-destructive downgrade support
    op.execute(
        """
        ALTER TABLE expert_verification_requests
        DROP COLUMN IF EXISTS payment_status,
        DROP COLUMN IF EXISTS payment_mode,
        DROP COLUMN IF EXISTS payment_amount,
        DROP COLUMN IF EXISTS crop,
        DROP COLUMN IF EXISTS diagnosis,
        DROP COLUMN IF EXISTS ai_confidence;
        """
    )
