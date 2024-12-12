# from blacksheep import json, Request
# from blacksheep.server.controllers import APIController
# from database.db import AsyncSession, async_engine
# from app.controllers.controllers import post
# from Models.models import MerchantTransactions
# from sqlmodel import select




# class ipg15WebhookController(APIController):

#     @classmethod
#     def class_name(cls) -> str:
#         return 'IPG15 Webhook Handler'
    
#     @classmethod
#     def route(cls) -> str | None:
#         return '/api/ipg/webhook/'
    

#     @post()
#     async def ipg15Webhook(self, request: Request):
#         """
#             For testing purposes.
#         """
#         try:
#             async with AsyncSession(async_engine) as session:
#                 form         = await request.form()

#                 order_status   = form['order_status']
#                 transaction_id = form['transID']
#                 status         = form['status']
#                 bill_amount    = form['bill_amt']
#                 date_time      = form['tdate']
#                 currency       = form['bill_currency']
#                 currency       = form['bill_currency']
#                 response       = form['response']
#                 payment_mode   = form['mop']
#                 card_no        = form['ccno']

#                 if response == 'Test Transaction succeeded, we do not charge any fees for testing transaction':
#                     merchant_transaction_obj = await session.execute(select(MerchantTransactions).where(
#                         MerchantTransactions.ipg_trans_id == transaction_id
#                     ))
#                     merchant_transaction = merchant_transaction_obj.scalar()

#                     if merchant_transaction:
#                         pass


#         except Exception as e:
#             return json({'msg': 'Server Error', 'msg': f'{str(e)}'}, 500)
