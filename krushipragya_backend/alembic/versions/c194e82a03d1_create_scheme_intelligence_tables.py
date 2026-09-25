"""create_scheme_intelligence_tables

Revision ID: c194e82a03d1
Revises: b82e14f05a9c
Create Date: 2026-09-26 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c194e82a03d1'
down_revision: Union[str, Sequence[str], None] = 'b82e14f05a9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update government_schemes: make published_by nullable and add provenance columns
    with op.batch_alter_table('government_schemes') as batch_op:
        batch_op.alter_column('published_by', nullable=True)
        batch_op.add_column(sa.Column('department', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('state', sa.String(length=100), server_default='Karnataka', nullable=True))
        batch_op.add_column(sa.Column('eligibility_kn', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('benefits_kn', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('application_process', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('application_process_kn', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('documents_required_kn', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('source_url', sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column('source_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('source_type', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('source_last_seen_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('source_last_modified_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('content_hash', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('last_crawled_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('crawler_status', sa.String(length=50), server_default='VERIFIED', nullable=True))
        batch_op.create_index('ix_government_schemes_state', ['state'])
        batch_op.create_index('ix_government_schemes_content_hash', ['content_hash'])

    # 2. scheme_sources
    op.create_table(
        'scheme_sources',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('base_url', sa.String(length=1000), nullable=False),
        sa.Column('domain_allowlist', sa.Text(), nullable=False),
        sa.Column('source_type', sa.String(length=100), server_default='CENTRAL_PORTAL', nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('crawl_priority', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # 3. scheme_crawl_runs
    op.create_table(
        'scheme_crawl_runs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('source_id', sa.UUID(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='RUNNING', nullable=False),
        sa.Column('pages_discovered', sa.Integer(), server_default='0', nullable=False),
        sa.Column('pages_crawled', sa.Integer(), server_default='0', nullable=False),
        sa.Column('schemes_found', sa.Integer(), server_default='0', nullable=False),
        sa.Column('schemes_created', sa.Integer(), server_default='0', nullable=False),
        sa.Column('schemes_updated', sa.Integer(), server_default='0', nullable=False),
        sa.Column('schemes_unchanged', sa.Integer(), server_default='0', nullable=False),
        sa.Column('schemes_failed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['scheme_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 4. scheme_source_documents
    op.create_table(
        'scheme_source_documents',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('scheme_id', sa.UUID(), nullable=True),
        sa.Column('source_id', sa.UUID(), nullable=True),
        sa.Column('source_url', sa.String(length=1000), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('raw_title', sa.String(length=500), nullable=True),
        sa.Column('extracted_content', sa.Text(), nullable=True),
        sa.Column('http_status', sa.Integer(), server_default='200', nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('parser_version', sa.String(length=50), server_default='1.0.0', nullable=False),
        sa.ForeignKeyConstraint(['scheme_id'], ['government_schemes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['source_id'], ['scheme_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_scheme_source_documents_hash', 'scheme_source_documents', ['content_hash'])

    # 5. scheme_user_state
    op.create_table(
        'scheme_user_state',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('scheme_id', sa.UUID(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_saved', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('saved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['government_schemes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'scheme_id', name='uq_scheme_user_state'),
    )
    op.create_index('ix_scheme_user_state_user', 'scheme_user_state', ['user_id'])
    op.create_index('ix_scheme_user_state_scheme', 'scheme_user_state', ['scheme_id'])


def downgrade() -> None:
    op.drop_table('scheme_user_state')
    op.drop_table('scheme_source_documents')
    op.drop_table('scheme_crawl_runs')
    op.drop_table('scheme_sources')

    with op.batch_alter_table('government_schemes') as batch_op:
        batch_op.drop_index('ix_government_schemes_content_hash')
        batch_op.drop_index('ix_government_schemes_state')
        batch_op.drop_column('crawler_status')
        batch_op.drop_column('last_verified_at')
        batch_op.drop_column('last_crawled_at')
        batch_op.drop_column('content_hash')
        batch_op.drop_column('source_last_modified_at')
        batch_op.drop_column('source_last_seen_at')
        batch_op.drop_column('source_type')
        batch_op.drop_column('source_name')
        batch_op.drop_column('source_url')
        batch_op.drop_column('documents_required_kn')
        batch_op.drop_column('application_process_kn')
        batch_op.drop_column('application_process')
        batch_op.drop_column('benefits_kn')
        batch_op.drop_column('eligibility_kn')
        batch_op.drop_column('state')
        batch_op.drop_column('department')
        batch_op.alter_column('published_by', nullable=False)
