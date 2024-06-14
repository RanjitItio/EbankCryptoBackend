"""MerchantGroup

Revision ID: 7ead8e690d9b
Revises: 
Create Date: 2024-06-08 10:52:34.672964

"""
from typing import Sequence, Union

from alembic import op
import sqlmodel
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ead8e690d9b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('merchantgroup',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.alter_column('merchantprofile', 'group',
               existing_type=sa.VARCHAR(),
               type_=sa.Integer(),
               existing_nullable=False)
    op.create_foreign_key(None, 'merchantprofile', 'merchantgroup', ['group'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'merchantprofile', type_='foreignkey')
    op.alter_column('merchantprofile', 'group',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    op.drop_table('merchantgroup')
    # ### end Alembic commands ###