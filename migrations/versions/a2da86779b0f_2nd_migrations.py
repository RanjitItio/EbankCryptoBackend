"""2nd migrations

Revision ID: a2da86779b0f
Revises: 
Create Date: 2024-04-30 15:10:19.815556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a2da86779b0f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('lastname', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('picture', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_email'), 'admin', ['email'], unique=True)
    op.create_table('currency',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('fee', sa.Float(), nullable=False),
    sa.Column('decimal_places', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('lastname', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('phoneno', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('default_wallets', sa.Integer(), nullable=True),
    sa.Column('address1', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('address2', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('city', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('state', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('country', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('picture', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('dogecoin_address', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('bitcoin_address', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('litcoin_address', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('is_merchent', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('externaltransection',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('txdid', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('txddate', sa.DateTime(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('txdtype', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('txdfee', sa.Float(), nullable=False),
    sa.Column('totalamount', sa.Float(), nullable=False),
    sa.Column('txdcurrency', sa.Integer(), nullable=False),
    sa.Column('recipientcurrency', sa.Integer(), nullable=False),
    sa.Column('recipientfullname', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('recipientemail', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('recipientmobile', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('recipientbanktransfer', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('recipientbankname', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('recipientbankaccountno', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('recipientbankifsc', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('recipientaddress', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['recipientcurrency'], ['currency.id'], ),
    sa.ForeignKeyConstraint(['txdcurrency'], ['currency.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_externaltransection_txdid'), 'externaltransection', ['txdid'], unique=True)
    op.create_table('transection',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('txdid', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('txddate', sa.DateTime(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('txdtype', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('txdfee', sa.Float(), nullable=False),
    sa.Column('totalamount', sa.Float(), nullable=False),
    sa.Column('txdcurrency', sa.Integer(), nullable=False),
    sa.Column('txdrecever', sa.Integer(), nullable=False),
    sa.Column('txdmassage', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('txdstatus', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['txdcurrency'], ['currency.id'], ),
    sa.ForeignKeyConstraint(['txdrecever'], ['users.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transection_txdid'), 'transection', ['txdid'], unique=True)
    op.create_table('wallet',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('currency_id', sa.Integer(), nullable=False),
    sa.Column('balance', sa.Float(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['currency_id'], ['currency.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('wallet')
    op.drop_index(op.f('ix_transection_txdid'), table_name='transection')
    op.drop_table('transection')
    op.drop_index(op.f('ix_externaltransection_txdid'), table_name='externaltransection')
    op.drop_table('externaltransection')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('currency')
    op.drop_index(op.f('ix_admin_email'), table_name='admin')
    op.drop_table('admin')
    # ### end Alembic commands ###
