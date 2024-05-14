"""create user table

Revision ID: f64ca5f0177f
Revises: 
Create Date: 2024-05-14 12:07:57.335599+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f64ca5f0177f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(128), nullable=False),
        sa.Column('password_hash', sa.String(128))
        )

def downgrade() -> None:
    op.drop_table('user')
