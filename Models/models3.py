from sqlmodel import SQLModel, Field




# Payment Button Table
class MerchantPaymentButton(SQLModel, table=True):
    id: int | None           = Field(primary_key=True, default=None)
    merchant_id: int | None  = Field(foreign_key='users.id', default=None, index=True)
    button_id: str           = Field(unique=True, index=True)
    button_title: str        = Field(default='')
    businessName: str        = Field(default='Business Name')
    fixedAmountLabel: str    = Field(default='', nullable=True)
    fixedAmount: float       = Field(default=0.00, nullable=True)
    customerAmountLabel: str = Field(default='', nullable=True)
    customerAmount: float    = Field(default=0.00, nullable=True)
    emailLabel: str          = Field(default='')
    phoneNoLable: str        = Field(default='')



# Payment Button styles table
class MerchantPaymentButtonStyles(SQLModel, table=True):
    id: int | None    = Field(primary_key=True, default=None)
    button_id: str    = Field(foreign_key='merchantpaymentbutton.button_id', index=True, unique=True)
    buttonLabel: str  = Field(default='Pay Now')
    buttonColor: str  = Field(default='white')
    buttonBgColor:str = Field(default='#2196f3')


