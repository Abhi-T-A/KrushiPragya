"""create_marketplace_transactions_table

Revision ID: d3cd77d7c3e1
Revises: d381f9a204e5
Create Date: 2026-09-26 06:51:32.049992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd3cd77d7c3e1'
down_revision: Union[str, Sequence[str], None] = 'd381f9a204e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create marketplace_transactions table idempotently and safely."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "marketplace_transactions" not in tables:
        op.create_table(
            "marketplace_transactions",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
                nullable=False,
            ),
            sa.Column(
                "offer_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("buyer_offers.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "listing_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("produce_listings.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "buyer_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("user_profiles.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "farmer_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("user_profiles.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "amount",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
            ),
            sa.Column(
                "currency",
                sa.String(length=10),
                server_default="INR",
                nullable=False,
            ),
            sa.Column(
                "idempotency_key",
                sa.String(length=120),
                nullable=True,
            ),
            sa.Column(
                "gateway_order_id",
                sa.String(length=120),
                nullable=True,
            ),
            sa.Column(
                "gateway_payment_id",
                sa.String(length=120),
                nullable=True,
            ),
            sa.Column(
                "gateway_signature",
                sa.String(length=255),
                nullable=True,
            ),
            sa.Column(
                "payment_status",
                sa.String(length=50),
                server_default="PAYMENT_PENDING",
                nullable=False,
            ),
            sa.Column(
                "order_status",
                sa.String(length=50),
                server_default="PENDING_PAYMENT",
                nullable=False,
            ),
            sa.Column(
                "failure_reason",
                sa.String(length=255),
                nullable=True,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

    # Ensure all indexes exist idempotently
    existing_indexes = (
        [idx["name"] for idx in inspector.get_indexes("marketplace_transactions")]
        if "marketplace_transactions" in tables
        else []
    )

    if "ix_marketplace_transactions_offer_id" not in existing_indexes:
        op.create_index(
            "ix_marketplace_transactions_offer_id",
            "marketplace_transactions",
            ["offer_id"],
            unique=False,
        )
    if "ix_marketplace_transactions_listing_id" not in existing_indexes:
        op.create_index(
            "ix_marketplace_transactions_listing_id",
            "marketplace_transactions",
            ["listing_id"],
            unique=False,
        )
    if "ix_marketplace_transactions_buyer" not in existing_indexes:
        op.create_index(
            "ix_marketplace_transactions_buyer",
            "marketplace_transactions",
            ["buyer_id"],
            unique=False,
        )
    if "ix_marketplace_transactions_farmer" not in existing_indexes:
        op.create_index(
            "ix_marketplace_transactions_farmer",
            "marketplace_transactions",
            ["farmer_id"],
            unique=False,
        )
    if "ix_marketplace_transactions_status" not in existing_indexes:
        op.create_index(
            "ix_marketplace_transactions_status",
            "marketplace_transactions",
            ["payment_status"],
            unique=False,
        )
    if "ix_marketplace_transactions_idempotency_key" not in existing_indexes:
        op.create_index(
            "ix_marketplace_transactions_idempotency_key",
            "marketplace_transactions",
            ["idempotency_key"],
            unique=True,
        )


def downgrade() -> None:
    """Downgrade schema: Drop marketplace_transactions table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "marketplace_transactions" in tables:
        op.drop_table("marketplace_transactions")
