"""first migration

Revision ID: 3d3bfa45f77d
Revises: 77218d1e2cdd
Create Date: 2024-05-01 17:32:46.056511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '3d3bfa45f77d'
down_revision: Union[str, None] = '77218d1e2cdd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('kycdetails',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('firstname', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('lastname', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('dateofbirth', sa.Date(), nullable=False),
    sa.Column('gander', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('marital_status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('phoneno', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('address', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('landmark', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('city', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('zipcode', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('state', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('country', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('nationality', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id_number', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id_expiry_date', sa.Date(), nullable=False),
    sa.Column('uploaddocument', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('kycdetails')
    # ### end Alembic commands ###
