"""create_crops_table

Revision ID: c917bfafa29c
Revises: 551865bd2180
Create Date: 2026-09-23 15:09:08.669273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c917bfafa29c'
down_revision: Union[str, Sequence[str], None] = '551865bd2180'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INITIAL_CROPS = [
    {
        "id": "c0000000-0000-4000-8000-000000000001",
        "code": "arecanut",
        "name_en": "Arecanut",
        "name_kn": "ಅಡಿಕೆ",
        "is_active": True,
    },
    {
        "id": "c0000000-0000-4000-8000-000000000002",
        "code": "paddy",
        "name_en": "Paddy",
        "name_kn": "ಭತ್ತ",
        "is_active": True,
    },
    {
        "id": "c0000000-0000-4000-8000-000000000003",
        "code": "black_pepper",
        "name_en": "Black Pepper",
        "name_kn": "ಕಾಳುಮೆಣಸು",
        "is_active": True,
    },
    {
        "id": "c0000000-0000-4000-8000-000000000004",
        "code": "cardamom",
        "name_en": "Cardamom",
        "name_kn": "ಏಲಕ್ಕಿ",
        "is_active": True,
    },
    {
        "id": "c0000000-0000-4000-8000-000000000005",
        "code": "coconut",
        "name_en": "Coconut",
        "name_kn": "ತೆಂಗು",
        "is_active": True,
    },
    {
        "id": "c0000000-0000-4000-8000-000000000006",
        "code": "turmeric",
        "name_en": "Turmeric",
        "name_kn": "ಅರಿಶಿನ",
        "is_active": True,
    },
    {
        "id": "c0000000-0000-4000-8000-000000000007",
        "code": "ginger",
        "name_en": "Ginger",
        "name_kn": "ಶುಂಠಿ",
        "is_active": True,
    },
]


def upgrade() -> None:
    """Create crops table and seed canonical crop records."""
    crops_table = op.create_table(
        'crops',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name_en', sa.String(length=100), nullable=False),
        sa.Column('name_kn', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='crops_pkey'),
        sa.UniqueConstraint('code', name='uq_crops_code')
    )
    op.create_index(op.f('ix_crops_code'), 'crops', ['code'], unique=True)

    # Insert deterministic initial canonical crops
    op.bulk_insert(crops_table, INITIAL_CROPS)


def downgrade() -> None:
    """Drop crops table and associated index."""
    op.drop_index(op.f('ix_crops_code'), table_name='crops')
    op.drop_table('crops')
