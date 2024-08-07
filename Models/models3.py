from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import event




# Payment Button Table
class MerchantPaymentButton(SQLModel, table=True):
    id: int | None              = Field(primary_key=True, default=None)
    merchant_id: int | None     = Field(foreign_key='users.id', default=None, index=True)
    button_id: str              = Field(unique=True, index=True)
    button_title: str           = Field(default='')
    businessName: str           = Field(default='Business Name')
    isFixedAmount: bool         = Field(default=False, nullable=True)
    fixedAmountLabel: str       = Field(default='', nullable=True)
    fixedAmount: float          = Field(default=0.00, nullable=True)
    fixedAmountCurrency: str    = Field(default='', nullable=True)
    isCustomerAmount: bool      = Field(default=False, nullable=True)
    customerAmountLabel: str    = Field(default='', nullable=True)
    customerAmount: float       = Field(default=0.00, nullable=True)
    customerAmountCurrency: str = Field(default='', nullable=True)
    emailLabel: str             = Field(default='')
    phoneNoLable: str           = Field(default='')
    cretedAt: datetime          = Field(default=datetime.now(), nullable=True)

    def assign_current_datetime(self):
        self.cretedAt = datetime.now()



# Payment Button styles table
class MerchantPaymentButtonStyles(SQLModel, table=True):
    id: int | None    = Field(primary_key=True, default=None)
    button_id: str    = Field(foreign_key='merchantpaymentbutton.button_id', index=True, unique=True)
    buttonLabel: str  = Field(default='Pay Now')
    buttonColor: str  = Field(default='white')
    buttonBgColor:str = Field(default='#2196f3')





# Auto assign current date and time when created
@event.listens_for(MerchantPaymentButton, 'before_insert')
def MerchantPaymentButton_time_listener(mapper, connection, target):
    target.assign_current_datetime()