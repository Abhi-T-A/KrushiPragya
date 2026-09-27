"""add_payu_fields_to_payment_transactions

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-09-26 11:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5a6b7c8d9e0'
down_revision: Union[str, Sequence[str], None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('payment_transactions') as batch_op:
        batch_op.add_column(sa.Column('provider', sa.String(length=50), server_default='payu', nullable=True))
        batch_op.add_column(sa.Column('merchant_transaction_id', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('provider_transaction_id', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('failure_reason', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
        batch_op.create_index('ix_payment_transactions_merchant_txnid', ['merchant_transaction_id'])


def downgrade() -> None:
    with op.batch_alter_table('payment_transactions') as batch_op:
        batch_op.drop_index('ix_payment_transactions_merchant_txnid')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('failure_reason')
        batch_op.drop_column('provider_transaction_id')
        batch_op.drop_column('merchant_transaction_id')
        batch_op.drop_column('provider')
