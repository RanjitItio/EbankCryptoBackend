"""is_suspended

Revision ID: cc619ce97f83
Revises: b6bbff0edc3c
Create Date: 2024-05-18 13:55:38.677410

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc619ce97f83'
down_revision: Union[str, None] = 'b6bbff0edc3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_currency_name'), 'currency', ['name'], unique=False)
    op.add_column('users', sa.Column('is_suspended', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'is_suspended')
    op.drop_index(op.f('ix_currency_name'), table_name='currency')
    # ### end Alembic commands ###