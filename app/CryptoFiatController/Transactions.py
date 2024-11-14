from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import Request, json
from Models.models import Currency, Users, Wallet
from Models.models4 import DepositTransaction, TransferTransaction
from Models.crypto import CryptoExchange, CryptoWallet
from Models.FIAT.Schema import UserFIATTransactionFilterSchema
from database.db import async_engine, AsyncSession
from app.controllers.controllers import get, post
from blacksheep.server.authorization import auth
from sqlmodel import select, and_, desc, func
from datetime import datetime, timedelta
from app.dateFormat import get_date_range
from sqlalchemy.orm import aliased







# All Fiat Transactions of a user
class UserFiatTransactionController(APIController):

    @classmethod
    def route(cls):
        return '/api/v4/users/fiat/transactions/'
    

    @classmethod
    def class_name(cls):
        return "User wise Transaction Controller"
    
    ### Get all Deposit, Transfer, Crypto Exchange Transactions
    @auth('userauth')
    @get()
    async def get_userTransaction(self, request: Request, limit: int = 5, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate user
                user_identity = request.identity
                user_id       = user_identity.claims.get("user_id") if user_identity else None

                ### Count Total available rows in Deposit table
                select_deposit_rows = select(func.count(DepositTransaction.id)).where(DepositTransaction.user_id == user_id)
                exec_select_deposit_rows = await session.execute(select_deposit_rows)
                total_deposit_rows = exec_select_deposit_rows.scalar()

                ### Count total available rows in Transfer table
                select_transfer_rows      = select(func.count(TransferTransaction.id)).where(TransferTransaction.user_id == user_id)
                exec_select_transfer_rows = await session.execute(select_transfer_rows)
                total_transfer_rows       = exec_select_transfer_rows.scalar()

                ### Count available rows in Crypto Exchange table
                ### Count all availble rows for paginated data
                select_exchange_rows = select(func.count(CryptoExchange.id)).where(CryptoExchange.user_id == user_id)
                exec_exchange_query  = await session.execute(select_exchange_rows)

                total_exchange_rows = exec_exchange_query.scalar()

                ## Count total avaible rows
                total_rows           = total_deposit_rows + total_transfer_rows + total_exchange_rows
                total_paginated_rows = total_rows / (limit * 3)

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

                #### Crypto Exchange Transactions
                stmt = select(
                    CryptoExchange.id,
                    CryptoExchange.user_id,
                    CryptoExchange.transaction_id,
                    CryptoExchange.created_at,
                    CryptoExchange.exchange_crypto_amount,
                    CryptoExchange.converted_fiat_amount,
                    CryptoExchange.status,
                    CryptoExchange.fee_value,

                    CryptoWallet.crypto_name,
                    Wallet.currency,
                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoExchange.crypto_wallet
                ).join(
                    Wallet, Wallet.id == CryptoExchange.fiat_wallet
                ).where(
                    CryptoExchange.user_id == user_id
                ).order_by(
                    desc(CryptoExchange.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                #### Get all available Crypto Exchange Transactions
                all_crypto_exchange_transaction_obj = await session.execute(stmt)
                all_crypto_exchange_transaction     = all_crypto_exchange_transaction_obj.fetchall()

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
                    ] + [
                        {
                            "type": "CryptoExchange",
                            "data": {
                                'id': transaction.id,
                                'user_id': transaction.user_id,
                                'transaction_id': transaction.transaction_id,
                                'created_At': transaction.created_at,
                                'amount': transaction.exchange_crypto_amount, ###exchange_crypto_amount
                                'credited_amount': transaction.converted_fiat_amount,
                                'status': transaction.status,
                                'transaction_fee': transaction.fee_value, ###transaction_fee
                                'crypto_name': transaction.crypto_name,
                                'credited_currency': transaction.currency,
                            },
                            'currency': {
                                    'name': transaction.currency
                            }
                        } for transaction in all_crypto_exchange_transaction
                    ]

                return json({
                    'message': 'Transaction data fetched successfully', 
                    'all_fiat_transactions': combined_transactions,
                    'total_paginated_rows': total_paginated_rows
                    }, 200)
                
        except Exception as e:
            return json({'error': f'{str(e)}'}, 500)
        


# User Recent Transactions
# Fiat recent Transactions
class UserFiatRecentTransactionController(APIController):

    @classmethod
    def route(cls):
        return '/api/v4/users/fiat/recent/transactions/'
    

    @classmethod
    def class_name(cls):
        return "User wise Transaction"
    

    @auth('userauth')
    @get()
    async def get_userTransaction(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate user
                user_identity = request.identity
                user_id       = user_identity.claims.get("user_id") if user_identity else None

                 # Get all deposit Transaction
                deposit_transaction_obj = await session.execute(select(DepositTransaction).where(
                    DepositTransaction.user_id == user_id
                ).order_by(
                    desc(DepositTransaction.id)
                ).limit(
                    5
                ).offset(
                    0
                ))
                deposit_transaction = deposit_transaction_obj.scalars().all()


                # Get all transfer transactions
                transfer_transaction_obj = await session.execute(select(TransferTransaction).where(
                    TransferTransaction.user_id == user_id
                ).order_by(
                    desc(TransferTransaction.id)
                ).limit(
                    5
                ).offset(
                    0
                ))
                transfer_transaction = transfer_transaction_obj.scalars().all()

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
                            "transaction": deposit,
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
                            "transaction": transfer,
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
                    'all_fiat_recent_transactions': combined_transactions
                    }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        



# All Fiat Transactions of a user
class UserFiatTransactionFilterController(APIController):

    @classmethod
    def route(cls):
        return '/api/v4/users/filter/fiat/transactions/'
    

    @classmethod
    def class_name(cls):
        return "Filter User Transaction Controller"
    

    @auth('userauth')
    @post()
    async def filter_userFIATTransaction(self, request: Request,schema: UserFIATTransactionFilterSchema,  limit: int = 5, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate user
                user_identity = request.identity
                user_id       = user_identity.claims.get("user_id") if user_identity else None


                #### Get the payload data
                dateRange       = schema.dateRange
                transactionType = schema.transaction_type
                filterCurrency  = schema.currency
                status          = schema.status
                startDate       = schema.start_date
                endDate         = schema.end_date

                deposit_conditions   = []
                transfer_conditions  = []
                crypto_exchange_conditions = []

                #### Aliased table
                TransferTransactionSender   = aliased(Users)

                ## Filter date range wise
                if dateRange and dateRange == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    deposit_conditions.append(
                        and_(
                            DepositTransaction.created_At >= start_date,
                            DepositTransaction.created_At < (end_date + timedelta(days=1))
                        )
                    )

                    transfer_conditions.append(
                        and_(
                            TransferTransaction.created_At >= start_date,
                            TransferTransaction.created_At < (end_date + timedelta(days=1))
                        )
                    )

                    crypto_exchange_conditions.append(
                        and_(
                            CryptoExchange.created_at >= start_date,
                            CryptoExchange.created_at < (end_date + timedelta(days=1))
                        )
                    )

                elif dateRange:
                    start_date, end_date = get_date_range(dateRange)

                    deposit_conditions.append(
                        and_(
                            DepositTransaction.created_At >= start_date,
                            DepositTransaction.created_At <= end_date
                        )
                    )

                    transfer_conditions.append(
                        and_(
                            TransferTransaction.created_At >= start_date,
                            TransferTransaction.created_At <= end_date
                        )
                    )

                    crypto_exchange_conditions.append(
                        and_(
                            CryptoExchange.created_at >= start_date,
                            CryptoExchange.created_at <= end_date
                        )
                    )
                
                ### Filter Currency Wise
                if filterCurrency:
                    currency_obj = await session.execute(select(Currency).where(
                        Currency.name == filterCurrency
                    ))
                    currency = currency_obj.scalar()

                    fiat_wallet__obj = await session.execute(select(Wallet).where(
                        and_(
                            Wallet.currency_id == currency.id,
                            Wallet.user_id == user_id
                        )
                    ))
                    fiat_wallet__obj = fiat_wallet__obj.scalar()

                    if not currency:
                        return json({'message': 'Invalid Currency'}, 404)
                    
                    deposit_conditions.append(
                        DepositTransaction.currency == currency.id
                    )

                    transfer_conditions.append(
                        TransferTransaction.currency == currency.id
                    )

                    crypto_exchange_conditions.append(
                        CryptoExchange.fiat_wallet == fiat_wallet__obj.id
                    )

                ### Filter Status wise
                if status:
                    deposit_conditions.append(
                        DepositTransaction.status == status
                    )

                    transfer_conditions.append(
                        TransferTransaction.status == status
                    )

                    crypto_exchange_conditions.append(
                        CryptoExchange.status == status
                    )
                
                #### Filter transaction Type wise
                if transactionType == 'Deposit' or not transactionType:
                    deposit_stmt = select(
                        DepositTransaction.id,
                        DepositTransaction.user_id,
                        DepositTransaction.transaction_id,
                        DepositTransaction.amount,
                        DepositTransaction.currency,
                        DepositTransaction.transaction_fee,
                        DepositTransaction.payout_amount,
                        DepositTransaction.status,
                        DepositTransaction.payment_mode,
                        DepositTransaction.is_completed,
                        DepositTransaction.selected_wallet,
                        DepositTransaction.credited_amount,
                        DepositTransaction.credited_currency,
                        DepositTransaction.created_At,

                        Currency.name.label('deposit_currency'),
                        Currency.id.label('deposit_currency_id'),

                        Users.first_name.label("deposit_user_first_name"),
                        Users.lastname.label("deposit_user_last_name"),
                        Users.id.label("deposit_user_id"),
                    ).join(
                        Currency, Currency.id == DepositTransaction.currency
                    ).join(
                        Users, Users.id == DepositTransaction.user_id
                    ).where(
                        DepositTransaction.user_id == user_id
                    )

                    if deposit_conditions:
                        deposit_stmt = deposit_stmt.where(and_(*deposit_conditions))

                    deposit_stmt = deposit_stmt.order_by(desc(DepositTransaction.id)).limit(limit).offset(offset)

                    # Count query
                    deposit_count_stmt = select(func.count()).select_from(DepositTransaction).where(DepositTransaction.user_id == user_id)

                    if deposit_conditions:
                        deposit_count_stmt = deposit_count_stmt.where(and_(*deposit_conditions))

                    # Execute the queries
                    deposit_count = (await session.execute(deposit_count_stmt)).scalar()

                    user_deposit_transaction_obj = await session.execute(deposit_stmt)
                    user_deposit_transaction     = user_deposit_transaction_obj.fetchall()

                else:
                    user_deposit_transaction = []
                    deposit_count = 0

                ### If transaction Type is equal to Transfer
                if transactionType == 'Transfer' or not transactionType:
                    transfer_stmt = select(
                        TransferTransaction.id,
                        TransferTransaction.user_id,
                        TransferTransaction.transaction_id,
                        TransferTransaction.receiver,
                        TransferTransaction.amount,
                        TransferTransaction.transaction_fee,
                        TransferTransaction.payout_amount,
                        TransferTransaction.currency,
                        TransferTransaction.massage,
                        TransferTransaction.status,
                        TransferTransaction.payment_mode,
                        TransferTransaction.receiver_payment_mode,
                        TransferTransaction.receiver_currency,
                        TransferTransaction.receiver_detail,
                        TransferTransaction.credited_amount,
                        TransferTransaction.credited_currency,
                        TransferTransaction.is_completed,
                        TransferTransaction.created_At,

                        Currency.name.label('transfer_currency'),
                        Currency.id.label('transfer_currency_id'),

                        TransferTransactionSender.first_name.label('sender_first_name'),
                        TransferTransactionSender.lastname.label('sender_last_name'),
                        TransferTransactionSender.id.label('sender_id'),

                    ).join(
                        Currency, Currency.id == TransferTransaction.currency
                    ).join(
                        TransferTransactionSender, TransferTransactionSender.id == TransferTransaction.user_id
                    ).where(
                        TransferTransaction.user_id == user_id
                    )

                    if transfer_conditions:
                        transfer_stmt = transfer_stmt.where(and_(*transfer_conditions))

                    transfer_stmt = transfer_stmt.order_by(desc(TransferTransaction.id)).limit(limit).offset(offset)

                    # Count query
                    transfer_count_stmt = select(func.count()).select_from(TransferTransaction).where(TransferTransaction.user_id == user_id)

                    if transfer_conditions:
                        transfer_count_stmt = transfer_count_stmt.where(and_(*transfer_conditions))

                    transfer_count  = (await session.execute(transfer_count_stmt)).scalar()

                    user_transfer_transaction_obj = await session.execute(transfer_stmt)
                    user_transfer_transaction     = user_transfer_transaction_obj.fetchall()

                else:
                    user_transfer_transaction = []
                    transfer_count = 0

                 ### Transaction Type wise filter
                if transactionType == 'CryptoExchange' or not transactionType:
                    crypto_exchange_stmt = select(
                        CryptoExchange.id,
                        CryptoExchange.user_id,
                        CryptoExchange.transaction_id,
                        CryptoExchange.created_at,
                        CryptoExchange.exchange_crypto_amount,
                        CryptoExchange.converted_fiat_amount,
                        CryptoExchange.status,
                        CryptoExchange.fee_value,

                        CryptoWallet.crypto_name,
                        Wallet.currency,
                    ).join(
                        CryptoWallet, CryptoWallet.id == CryptoExchange.crypto_wallet
                    ).join(
                        Wallet, Wallet.id == CryptoExchange.fiat_wallet
                    ).where(
                        CryptoExchange.user_id == user_id
                    )

                    if crypto_exchange_conditions:
                        crypto_exchange_stmt = crypto_exchange_stmt.where(and_(*crypto_exchange_conditions))
                        
                    crypto_exchange_stmt = crypto_exchange_stmt.order_by(desc(CryptoExchange.id)).limit(limit).offset(offset)

                    # Count query
                    exchang_count_stmt = select(func.count()).select_from(CryptoExchange).where(CryptoExchange.user_id == user_id)

                    if crypto_exchange_conditions:
                        exchang_count_stmt = exchang_count_stmt.where(and_(*crypto_exchange_conditions))

                    exchange_count  = (await session.execute(exchang_count_stmt)).scalar()

                    user_exchange_transaction_obj = await session.execute(crypto_exchange_stmt)
                    user_exchange_transaction     = user_exchange_transaction_obj.fetchall()
                
                else:
                    user_exchange_transaction = []
                    exchange_count = 0

                ### If noo data found
                if not user_transfer_transaction and not user_deposit_transaction and not user_exchange_transaction:
                    return json({"message": 'No data found'}, 404)
                
                ### Count Paginated value
                total_deposit_transfer_count = deposit_count + transfer_count + exchange_count
                paginated_count = total_deposit_transfer_count / (limit * 3) if limit > 0 else 1

                ### Get Receiver Data
                all_user_obj      = await session.execute(select(Users))
                all_user_obj_data = all_user_obj.scalars().all()

                receiver_dict = { receiver.id: receiver for receiver in all_user_obj_data }

                ### Append all data inside a list
                combined_transactions = [
                        {
                            "type": "Deposit", 
                            "data": deposit._asdict(),
                            "currency": {
                                "id": deposit.deposit_currency_id,
                                "name": deposit.deposit_currency,
                            },
                            "user": {
                                "first_name": deposit.deposit_user_first_name,
                                "lastname": deposit.deposit_user_last_name,
                                "id": deposit.deposit_user_id
                            },
                            "receiver": None

                        } for deposit in user_deposit_transaction

                    ] + [
                        {
                            "type": "Transfer", 
                            "data": transfer._asdict(),
                            "currency": {
                                "id": transfer.transfer_currency_id,
                                "name": transfer.transfer_currency,
                            },
                            "user": {
                                    "first_name": transfer.sender_first_name,
                                    "lastname": transfer.sender_last_name,
                                    "id": transfer.sender_id
                                },
                            "receiver": {
                                "first_name": receiver_dict[transfer.receiver].first_name,
                                "lastname": receiver_dict[transfer.receiver].lastname,
                                "id": receiver_dict[transfer.receiver].id
                            } if transfer.receiver in receiver_dict else None, 

                         } for transfer in user_transfer_transaction

                    ] + [
                        {
                            "type": "CryptoExchange",
                            "data": {
                                'id': transaction.id,
                                'user_id': transaction.user_id,
                                'transaction_id': transaction.transaction_id,
                                'created_At': transaction.created_at,
                                'amount': transaction.exchange_crypto_amount, ###exchange_crypto_amount
                                'credited_amount': transaction.converted_fiat_amount,
                                'status': transaction.status,
                                'transaction_fee': transaction.fee_value, ###transaction_fee
                                'crypto_name': transaction.crypto_name,
                                'credited_currency': transaction.currency,
                            },
                            'currency': {
                                    'name': transaction.currency
                            }
                        } for transaction in user_exchange_transaction
                    ]
                
                return json({
                    'success': True,
                    'filtered_user_fiat_transaction': combined_transactions,
                    'paginated_count': paginated_count

                }, 200)


        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



