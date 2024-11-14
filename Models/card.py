from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import event



#### FIAT Card Table
class FiatCard(SQLModel, table=True):
    id: int | None       = Field(default=None, primary_key=True)
    user_id: int         = Field(default=None, foreign_key='users.id', index=True)
    card_name: str       = Field(nullable=True)
    card_number: str     = Field(index=True, default=None, unique=True)
    currency: int        = Field(foreign_key='currency.id')
    valid_from: datetime = Field(default=None)
    valid_thru: datetime = Field(default=None)
    created_at: datetime = Field(default=datetime.now())
    cvv: str             = Field(default=None)
    pin: str             = Field(default=None)
    status: str          = Field(nullable=True)

    def assign_current_datetime(self):
        self.created_at = datetime.now()



## Assign current date time when Card created
@event.listens_for(FiatCard, 'before_insert')
def assign_fiat_card_time_listener(mapper, connection, target):
    target.assign_current_datetime()
