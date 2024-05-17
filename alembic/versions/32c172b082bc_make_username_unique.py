"""make username unique

Revision ID: 32c172b082bc
Revises: 5cf167bffb72
Create Date: 2024-05-16 13:04:40.686122+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32c172b082bc'
down_revision: Union[str, None] = '5cf167bffb72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('unique_username', 'user', ['username'])


def downgrade() -> None:
    op.drop_constraint('unique_username', 'user', type_='unique')

