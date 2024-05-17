"""ipaddress

Revision ID: b6bbff0edc3c
Revises: 3a7fe7198d28
Create Date: 2024-05-15 17:33:51.464575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b6bbff0edc3c'
down_revision: Union[str, None] = '3a7fe7198d28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('ipaddress', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'ipaddress')
    # ### end Alembic commands ###