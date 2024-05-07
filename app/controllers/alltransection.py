from blacksheep.server.controllers import post, APIController
from Models.schemas import TransferMoneySchema , ExternalTransectionSchema ,WithdrawlAndDeposieSchema ,getdata
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users ,Wallet ,Transection ,Currency , ExternalTransection
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
import time
import uuid


class AllTransactionController(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/all-transactions'

    @classmethod
    def class_name(cls):
        return "All Transactions Controller"

    @post()
    async def get_all_transactions(self,data:getdata, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # Get the user ID from the request
                # user_id = decode_token(request.headers.get("Authorization"))["user_id"]

                # Fetch all transactions for the user
                transactions = await session.execute(select(Transection).where(Transection.user_id == data.user_id))
                transactions_list = transactions.scalars().all()
                # Fetch all external transactions for the user
                external_transactions = await session.execute(select(ExternalTransection).where(ExternalTransection.user_id == data.user_id))
                
                external_transactions_list = external_transactions.scalars().all()
                # Combine the transactions and external transactions
                all_transactions = transactions_list + external_transactions_list
                # Convert the transactions to a JSON-serializable format
                # transactions_data = []
                # for transaction in all_transactions:
                #     transaction_data = {
                #         "id": transaction.txdid,
                #         "type": transaction.txdtype,
                #         "receiver": transaction.txdrecever,
                #         "amount": transaction.amount,
                #         "fee": transaction.txdfee,
                #         "total_amount": transaction.totalamount,
                #         "currency": transaction.txdcurrency,
                #         "message": transaction.txdmassage,
                #         "created_at": transaction.created_at.isoformat()
                
                return json(all_transactions, status=200)
        except SQLAlchemyError as e:
            return json({"message": str(e)}, status=500)
                        