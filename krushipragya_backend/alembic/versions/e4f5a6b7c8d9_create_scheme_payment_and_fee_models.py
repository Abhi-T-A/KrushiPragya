"""create_scheme_payment_and_fee_models

Revision ID: e4f5a6b7c8d9
Revises: d3cd77d7c3e1
Create Date: 2026-09-26 07:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, Sequence[str], None] = 'd3cd77d7c3e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add scheme fee model columns to government_schemes
    with op.batch_alter_table('government_schemes') as batch_op:
        batch_op.add_column(sa.Column('official_fee', sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column('krushipragya_service_fee', sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column('payment_required', sa.Boolean(), server_default=sa.text('false'), nullable=False))
        batch_op.add_column(sa.Column('fee_type', sa.String(length=50), server_default='UNKNOWN', nullable=False))
        batch_op.add_column(sa.Column('fee_description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('fee_source', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('fee_last_verified', sa.DateTime(timezone=True), nullable=True))

    # 2. Add columns to scheme_applications
    with op.batch_alter_table('scheme_applications') as batch_op:
        batch_op.add_column(sa.Column('payment_status', sa.String(length=50), server_default='NOT_REQUIRED', nullable=False))
        batch_op.add_column(sa.Column('payment_transaction_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))

    # 3. Create generic payment_transactions table (supporting SCHEME_APPLICATION and MARKETPLACE)
    op.create_table(
        'payment_transactions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), server_default='SCHEME_APPLICATION', nullable=False),
        sa.Column('farmer_id', sa.UUID(), nullable=False),
        sa.Column('scheme_id', sa.UUID(), nullable=True),
        sa.Column('application_id', sa.UUID(), nullable=True),
        sa.Column('official_fee', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False),
        sa.Column('service_fee', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='INR', nullable=False),
        sa.Column('payment_method', sa.String(length=50), server_default='PHONEPE_STATIC_QR', nullable=False),
        sa.Column('payment_status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('payment_reference', sa.String(length=100), nullable=True),
        sa.Column('refund_status', sa.String(length=50), server_default='NOT_APPLICABLE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by', sa.UUID(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('receipt_data', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['farmer_id'], ['user_profiles.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['scheme_id'], ['government_schemes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['application_id'], ['scheme_applications.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['verified_by'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_reference', name='uq_payment_transactions_reference'),
    )
    op.create_index('ix_payment_transactions_farmer', 'payment_transactions', ['farmer_id'])
    op.create_index('ix_payment_transactions_scheme', 'payment_transactions', ['scheme_id'])
    op.create_index('ix_payment_transactions_application', 'payment_transactions', ['application_id'])
    op.create_index('ix_payment_transactions_status', 'payment_transactions', ['payment_status'])

    # 4. Foreign key link from scheme_applications to payment_transactions
    op.create_foreign_key(
        'fk_scheme_applications_payment_transaction',
        'scheme_applications',
        'payment_transactions',
        ['payment_transaction_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_scheme_applications_payment_transaction', 'scheme_applications', type_='foreignkey')
    op.drop_table('payment_transactions')

    with op.batch_alter_table('scheme_applications') as batch_op:
        batch_op.drop_column('created_at')
        batch_op.drop_column('payment_transaction_id')
        batch_op.drop_column('payment_status')

    with op.batch_alter_table('government_schemes') as batch_op:
        batch_op.drop_column('fee_last_verified')
        batch_op.drop_column('fee_source')
        batch_op.drop_column('fee_description')
        batch_op.drop_column('fee_type')
        batch_op.drop_column('payment_required')
        batch_op.drop_column('krushipragya_service_fee')
        batch_op.drop_column('official_fee')
