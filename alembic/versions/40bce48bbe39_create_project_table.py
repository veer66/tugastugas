"""create project table

Revision ID: 40bce48bbe39
Revises: f64ca5f0177f
Create Date: 2024-05-14 15:18:32.975916+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = '40bce48bbe39'
down_revision: Union[str, None] = 'f64ca5f0177f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'project',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.column('user_id', sa.Integer, ForeignKey('user.id')),
        sa.column('title', sa.String),
        sa.Column('data', JSONB)
        )

def downgrade() -> None:
    op.drop_table('project')
