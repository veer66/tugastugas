"""rename data field to content

Revision ID: 5cf167bffb72
Revises: b6f148ed96f6
Create Date: 2024-05-16 07:14:01.614647+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5cf167bffb72'
down_revision: Union[str, None] = 'b6f148ed96f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('project', 'data', new_column_name='content')


def downgrade() -> None:
    op.alter_column('project', 'content', new_column_name='data')
