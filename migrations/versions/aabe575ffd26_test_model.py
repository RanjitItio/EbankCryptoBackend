"""test_model

Revision ID: aabe575ffd26
Revises: 47b9343e09b0
Create Date: 2024-05-31 16:00:23.832126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'aabe575ffd26'
down_revision: Union[str, None] = '47b9343e09b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('testmodel', sa.Column('currency', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('testmodel', sa.Column('test_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('testmodel', 'test_id')
    op.drop_column('testmodel', 'currency')
    # ### end Alembic commands ###
