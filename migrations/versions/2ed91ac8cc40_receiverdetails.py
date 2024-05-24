"""receiverdetails

Revision ID: 2ed91ac8cc40
Revises: 6a22362b86f9
Create Date: 2024-05-23 16:02:58.743454

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '2ed91ac8cc40'
down_revision: Union[str, None] = '6a22362b86f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('receiverdetails',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('mobile_number', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('pay_via', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('bank_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('acc_number', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('ifsc_code', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('add_info', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('address', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('card_number', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('card_cvv', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('card_expiry', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('senderdetails',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bank_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('acc_number', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('ifsc_code', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('add_info', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('address', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('card_number', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('card_cvv', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('card_expiry', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('transection', sa.Column('rec_currency', sa.Integer(), nullable=True))
    op.add_column('transection', sa.Column('rec_detail', sa.Integer(), nullable=True))
    op.add_column('transection', sa.Column('send_detail', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'transection', 'senderdetails', ['send_detail'], ['id'])
    op.create_foreign_key(None, 'transection', 'receiverdetails', ['rec_detail'], ['id'])
    op.create_foreign_key(None, 'transection', 'currency', ['rec_currency'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'transection', type_='foreignkey')
    op.drop_constraint(None, 'transection', type_='foreignkey')
    op.drop_constraint(None, 'transection', type_='foreignkey')
    op.drop_column('transection', 'send_detail')
    op.drop_column('transection', 'rec_detail')
    op.drop_column('transection', 'rec_currency')
    op.drop_table('senderdetails')
    op.drop_table('receiverdetails')
    # ### end Alembic commands ###
