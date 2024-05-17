# from pydantic import BaseModel
# from datetime import datetime






# class AllTransactionCurrencySchema(BaseModel):
#     id: int
#     name: str
#     fee: float
#     symbol: str


# class AllTransactionUserSchema(BaseModel):
#     id: int
#     first_name: str
#     last_name: str


# class AllTransactionResponseSchema(BaseModel):
#     id: int 
#     user_id: int
#     txdid: str                 
#     txddate: datetime
#     txdtime: datetime           
#     amount: float              
#     txdcurrency: int            
#     txdfee: float               
#     totalamount:float          
#     txdrecever: int            
#     txdmassage: str            
#     txdstatus: str          
#     payment_mode: str 
#     txdtype: str 
#     currency: AllTransactionCurrencySchema
#     user:    AllTransactionUserSchema