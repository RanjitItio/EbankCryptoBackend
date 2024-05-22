"""Walletdateformatchange

Revision ID: 021f86c756b7
Revises: e469bfb251fd
Create Date: 2024-05-22 09:51:33.912023

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '021f86c756b7'
down_revision: Union[str, None] = 'e469bfb251fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('testmodel', sa.Column('created_time', sa.DateTime(), nullable=True))
    op.alter_column('wallet', 'created_data',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.Date(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('wallet', 'created_data',
               existing_type=sa.Date(),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
    op.drop_column('testmodel', 'created_time')
    # ### end Alembic commands ###