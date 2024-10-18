from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import event



## FEE STRUCTURE TABLE
class FeeStructure(SQLModel, table=True):
    id: int | None       = Field(primary_key=True)
    name: str            = Field(default='', unique=True, nullable=False) ## Crypto Buy, Crypto Sell, Exchange, Debit, Deposit
    fee_type: str        = Field(default='')
    tax_rate: float      = Field(default=0.00, nullable=True)
    min_value: float     = Field(default=0.00, nullable=True)
    created_at: datetime = Field(default=datetime.now(), nullable=True)



# Event listener for before insert
@event.listens_for(FeeStructure, "before_insert")
def before_insert(mapper, connection, target):
    target.created_at = datetime.now()


# Event listener for before update
@event.listens_for(FeeStructure, "before_update")
def before_update(mapper, connection, target):
    target.created_at = datetime.now()


