from sqlmodel import SQLModel, Field



## FEE STRUCTURE TABLE
class FeeStructure(SQLModel, table=True):
    id: int | None   = Field(primary_key=True)
    name: str        = Field(default='', unique=True) ## Crypto Buy, Crypto Sell, Exchange, Debit, Deposit
    fee_type: str    = Field(default='')
    tax_rate: float  = Field(default=0.00, nullable=True)
    min_value: float = Field(default=0.00, nullable=True)
