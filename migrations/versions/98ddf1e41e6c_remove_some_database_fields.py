"""remove some database fields

Revision ID: 98ddf1e41e6c
Revises: 828fff51d5d3
Create Date: 2024-04-17 16:51:08.324144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98ddf1e41e6c'
down_revision: Union[str, None] = '828fff51d5d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'city')
    op.drop_column('users', 'default_wallets')
    op.drop_column('users', 'bitcoin_address')
    op.drop_column('users', 'state')
    op.drop_column('users', 'address1')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'address2')
    op.drop_column('users', 'picture')
    op.drop_column('users', 'country')
    op.drop_column('users', 'litcoin_address')
    op.drop_column('users', 'dogecoin_address')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('dogecoin_address', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('litcoin_address', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('country', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('picture', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('address2', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('address1', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('state', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('bitcoin_address', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('default_wallets', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('city', sa.VARCHAR(), autoincrement=False, nullable=False))
    # ### end Alembic commands ###
