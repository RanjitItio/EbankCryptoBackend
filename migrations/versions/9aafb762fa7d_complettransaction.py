"""completTransaction

Revision ID: 9aafb762fa7d
Revises: a4be2f0fbcb1
Create Date: 2024-05-14 14:51:13.936768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9aafb762fa7d'
down_revision: Union[str, None] = 'a4be2f0fbcb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transection', sa.Column('is_completed', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transection', 'is_completed')
    # ### end Alembic commands ###