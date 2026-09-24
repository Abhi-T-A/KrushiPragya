"""create_crop_report_diagnoses_table

Revision ID: 4c187068455c
Revises: a749dc1e3ab3
Create Date: 2026-09-24 23:29:24.946594

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4c187068455c'
down_revision: Union[str, Sequence[str], None] = 'a749dc1e3ab3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'crop_report_diagnoses',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('crop_report_id', sa.UUID(), nullable=False),
        sa.Column('crop', sa.String(length=50), nullable=False),
        sa.Column('predicted_class', sa.String(length=100), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('predictions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['crop_report_id'], ['crop_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_crop_report_diagnoses_crop_report_id_created_at',
        'crop_report_diagnoses',
        ['crop_report_id', sa.text('created_at DESC')],
        unique=False,
    )
    op.create_index(
        op.f('ix_crop_report_diagnoses_predicted_class'),
        'crop_report_diagnoses',
        ['predicted_class'],
        unique=False,
    )
    op.create_index(
        op.f('ix_crop_report_diagnoses_crop'),
        'crop_report_diagnoses',
        ['crop'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_crop_report_diagnoses_crop'), table_name='crop_report_diagnoses')
    op.drop_index(op.f('ix_crop_report_diagnoses_predicted_class'), table_name='crop_report_diagnoses')
    op.drop_index('ix_crop_report_diagnoses_crop_report_id_created_at', table_name='crop_report_diagnoses')
    op.drop_table('crop_report_diagnoses')
