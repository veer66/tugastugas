"""set from_undo default

Revision ID: 0e3edbd17f92
Revises: e5fd722882aa
Create Date: 2024-05-19 06:22:53.859076+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import false

# revision identifiers, used by Alembic.
revision: str = '0e3edbd17f92'
down_revision: Union[str, None] = 'e5fd722882aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('task',
                    'from_undo',
                    existing_type=sa.BOOLEAN(),
                    nullable=False,
                    server_default=false())


def downgrade() -> None:
    op.alter_column('task',
                    'from_undo',
                    existing_type=sa.BOOLEAN(),
                    nullable=True,
                    server_default=None)
