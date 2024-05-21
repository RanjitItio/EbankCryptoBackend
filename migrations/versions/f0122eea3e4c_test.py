"""test

Revision ID: f0122eea3e4c
Revises: ae6346544c42
Create Date: 2024-05-21 14:25:19.837121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0122eea3e4c'
down_revision: Union[str, None] = 'ae6346544c42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('testmodel',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_date', sa.Date(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('testmodel')
    # ### end Alembic commands ###
