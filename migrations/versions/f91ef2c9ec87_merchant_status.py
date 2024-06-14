"""merchant_status

Revision ID: f91ef2c9ec87
Revises: 31c0c2172f02
Create Date: 2024-06-13 17:18:07.189817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'f91ef2c9ec87'
down_revision: Union[str, None] = '31c0c2172f02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('merchanttransactions', sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('merchanttransactions', 'status')
    # ### end Alembic commands ###
