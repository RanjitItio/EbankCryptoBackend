from blacksheep import json, redirect, Request, FromForm, FromJSON
from blacksheep.server.controllers import APIController
from app.controllers.controllers import get, post
from blacksheep.cookies import Cookie
from dataclasses import dataclass
from database.db import AsyncSession, async_engine
from Models.Merchant.schema import MerchantFormTransaction
from Models.models import BusinessProfile, MerchantTransactions, Currency
from sqlmodel import select


@dataclass
class InputForm:
    merchant: str
    merchant_id: str
    item_name: str
    order_number: str
    amount: str
    custom: str




# class PaymentPageRedirectController(APIController):

#     @classmethod
#     def class_name(cls) -> str:
#         return 'Payment Page Redirect'
    
#     @classmethod
#     def route(cls) -> str | None:
#         return '/api/payment/form/'
    
#     @post()
#     async def payment_redirect(self, request: Request):
#         request_form = await request.form()

#         print(request_form)
#         response = redirect('http://localhost:5173/payment/form')
            
#         return response
        



class MerchantPaymentController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Payment Form'

    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/user/merchant/payment/'
    
    @post()
    async def merchant_payment(self, request: Request, input: FromJSON[MerchantFormTransaction]):
        """
            This function processes a merchant payment transaction by fetching merchant and currency
            information, creating a transaction record, and handling potential errors.<br/><br/>
            
            Parameters:<br/>
            - request (Request): The incoming request object containing the payment data.<br/>
            - input (FromJSON[MerchantFormTransaction]): The JSON object representing the
            - MerchantFormTransaction` data received from the server.<br/><br/>
            
            Returns:<br/>
            - JSON: A JSON response containing the success message and status code 200 if the
              payment is successful.<br/>
            - If there are any errors during the process, it will return a JSON response with an error message and the corresponding status code (404, 400, or 500).<br/><br/>

            Raises:<br/>
            - ValueError: If the input data is not valid.<br/>
            - Exception: If there is an error while executing the SQL queries.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                data = input.value

                merchant_id = data.merchant_id
                item        = data.item
                order_id    = data.order_id
                amount      = data.amount
                currency    = data.currency
                #Get the merchant 
                try:
                    merchant_obj = await session.execute(select(BusinessProfile).where(
                        BusinessProfile.id == merchant_id
                    ))
                    merchant_obj_data = merchant_obj.scalar()

                    if not merchant_obj_data:
                        return json({'msg': 'Requested merchant not available'}, 404)
                    
                    merchant_fee = merchant_obj_data.fee
                    
                except Exception as e:
                    return json({'msg': 'Merchant fetch error'}, 400)
                
                try:
                    currency_obj      = await session.execute(select(Currency).where(Currency.name == currency))
                    currency_obj_data = currency_obj.scalar()
                except Exception as e:
                    return json({'msg': 'Currency error', 'error': f'{str(e)}'}, 400)
                
                #Calculate Amount to be credited if the status is success

                #Create merchant Transaction
                merchant_transaction = MerchantTransactions(
                    merchant = merchant_obj_data.id,
                    product  = item,
                    order_id = order_id,
                    amount   = amount,
                    currency = currency_obj_data.id
                )

                return json({'msg': 'Success'}, 200)

        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)