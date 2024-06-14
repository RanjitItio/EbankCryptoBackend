"""nullgroup

Revision ID: d9f2f24a2ce3
Revises: cf3527eeb9e1
Create Date: 2024-06-10 10:51:33.377787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9f2f24a2ce3'
down_revision: Union[str, None] = 'cf3527eeb9e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('merchantprofile', 'group',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('merchantprofile', 'group',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###