from app.controllers.controllers import get
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_, desc, func
from Models.models4 import DepositTransaction, TransferTransaction
from Models.models import Currency, Users







### FIAT Transactions Controller
class AdminUserFiatTransactionController(APIController):

    @classmethod
    def route(cls):
        return '/api/v4/admin/user/fiat/transactions/'
    
    @classmethod
    def class_name(cls):
        return "User wise Transaction"


    @auth('userauth')
    @get()
    async def get_userTransaction(self, request: Request, query: int, limit: int = 5, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate user
                admin_identity = request.identity
                admin_id       = admin_identity.claims.get("user_id") if admin_identity else None

                user_id = query

                # Admin authnetication
                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Admin authorization failed'}, 401)
                # Admin authentication ends

                # Get all deposit Transaction
                deposit_transaction_obj = await session.execute(select(DepositTransaction).where(
                    DepositTransaction.user_id == user_id
                ).order_by(
                    desc(DepositTransaction.id)
                ).limit(
                    limit
                ).offset(
                    offset
                ))
                deposit_transaction = deposit_transaction_obj.scalars().all()

                # Get all transfer transactions
                transfer_transaction_obj = await session.execute(select(TransferTransaction).where(
                    TransferTransaction.user_id == user_id
                ).order_by(
                    desc(TransferTransaction.id)
                ).limit(
                    limit
                ).offset(
                    offset
                ))
                transfer_transaction = transfer_transaction_obj.scalars().all()

                # Count Total rows of Deposit transactions
                deposit_stmt         = select(func.count(DepositTransaction.id))
                execute_deposit_rows = await session.execute(deposit_stmt)
                deposit_rows = execute_deposit_rows.scalar()

                # Count Total transfer rows
                transfer_stmt = select(func.count(TransferTransaction.id))
                exe_transfer_rows = await session.execute(transfer_stmt)
                transfer_rows     = exe_transfer_rows.scalar()

                total_rows = deposit_rows + transfer_rows

                total_row_count = total_rows / (limit * 2)

                # Fetch all the available Currencies
                currency     = await session.execute(select(Currency))
                currency_obj = currency.scalars().all()

                # Fetch all the available users
                all_user_obj      = await session.execute(select(Users))
                all_user_obj_data = all_user_obj.scalars().all()

                # Store inside a Dict
                currency_dict = {currency.id: currency for currency in currency_obj}
                user_dict     = {user.id: user         for user     in all_user_obj_data}
                receiver_dict = {receiver.id: receiver for receiver in all_user_obj_data}

                # Deposit data
                deposit_currency_data = (currency_dict.get(transaction.currency) for transaction in deposit_transaction)
                deposit_user_data     = (user_dict.get(transaction.user_id) for transaction in deposit_transaction)

                # Transfer Data
                transfer_currency_data = (currency_dict.get(transaction.currency) for transaction in transfer_transaction)
                transfer_sender_data   = (user_dict.get(transaction.user_id) for transaction in transfer_transaction)
                transfer_receiver_data = (receiver_dict.get(transaction.receiver) for transaction in transfer_transaction)

                # Combine all the data
                deposit_data_combined  = zip(deposit_transaction, deposit_currency_data, deposit_user_data)
                transfer_data_combined = zip(transfer_transaction, transfer_currency_data, transfer_sender_data, transfer_receiver_data)
                

                combined_transactions = [
                        {
                            "type": "Deposit", 
                            "data": deposit,
                            "currency": currency,
                            "user": {
                                "first_name": user.first_name,
                                "lastname": user.lastname,
                                "id": user.id
                            },
                            "receiver": None
                            } for deposit, currency, user in deposit_data_combined
                    ] + [
                        {
                            "type": "Transfer", 
                            "data": transfer,
                            "currency": currency,
                            "user": {
                                    "first_name": sender.first_name,
                                    "lastname": sender.lastname,
                                    "id": sender.id
                                },
                            "receiver": {
                                "first_name": receiver.first_name,
                                "lastname": receiver.lastname,
                                "id": receiver.id
                            } if receiver else None, 

                         } for transfer, currency, sender, receiver in transfer_data_combined
                    ]

                return json({
                    'message': 'Transaction data fetched successfully', 
                    'all_user_fiat_transactions': combined_transactions,
                    'total_row_count': total_row_count
                    }, 200)

        except Exception as e:
            return json({'error': f'{str(e)}'}, 500)