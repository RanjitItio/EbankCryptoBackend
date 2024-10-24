from blacksheep import json, Request, pretty_json, FromJSON
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from app.controllers.controllers import get, put, post
from database.db import AsyncSession, async_engine
from Models.models import Users, Currency, Wallet
from Models.models4 import DepositTransaction
from Models.schemas import UpdateTransactionSchema
from Models.FIAT.Schema import AdminFilterFIATDeposits
from sqlmodel import select, desc, func, and_
from decouple import config
from httpx import AsyncClient
from app.dateFormat import get_date_range



currency_converter_api = config('CURRENCY_CONVERTER_API')
RAPID_API_KEY          = config('RAPID_API_KEY')
RAPID_API_HOST         = config('RAPID_API_HOST')




#Admin will be able to view all the Deposits
class AllDepositController(APIController):

    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/deposits/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'All Deposits'
    
    @auth('userauth')
    @get()
    async def get_deposite_transaction(self, request: Request, limit: int = 10, offset: int = 0):
        """
          View all the Deposit Transactions, By Admin
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id') if user_identity else None

                limit  = limit
                offset = offset

                # Admin authentication
                admin_obj     = await session.execute(select(Users).where(Users.id == admin_id))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data.is_admin:
                    return json({'msg': 'Admin authorization Failed'}, 401)
                # Admin authentication ends

                # Count total rows in the table
                count_stmt          = select(func.count(DepositTransaction.id))
                total_deposite_obj  = await session.execute(count_stmt)
                total_deposite_rows = total_deposite_obj.scalar()

                total_deposit_row_count = total_deposite_rows / limit

                stmt  = select(
                    DepositTransaction.id,
                    DepositTransaction.transaction_id,
                    DepositTransaction.created_At,
                    DepositTransaction.amount,
                    DepositTransaction.transaction_fee,
                    DepositTransaction.payout_amount,
                    DepositTransaction.status,
                    DepositTransaction.payment_mode,
                    DepositTransaction.is_completed,

                    Users.full_name,
                    Users.email,
                    Currency.name.label('currency_name')

                    ).join(
                        Users,  Users.id == DepositTransaction.user_id
                    ).join(
                        Currency, Currency.id == DepositTransaction.currency
                    ).order_by(
                        desc(DepositTransaction.id)
                    ).limit(
                        limit
                    ).offset(
                        offset
                    )
                
                #Get all transaction Data
                get_all_transaction     = await session.execute(stmt)
                get_all_transaction_obj = get_all_transaction.all()
                
                combined_data = []

                if not get_all_transaction_obj:
                    return json({'msg': "No Transaction available"}, 404)
                
                for transaction in get_all_transaction_obj:

                        combined_data.append({
                            'id': transaction.id,
                            'transaction_id': transaction.transaction_id,
                            'created_At': transaction.created_At,
                            'amount': transaction.amount,
                            'transaction_fee': transaction.transaction_fee,
                            'payout_amount': transaction.payout_amount,
                            'status': transaction.status,
                            'payment_mode': transaction.payment_mode,
                            'is_completed': transaction.is_completed,
                            'user_name': transaction.full_name,
                            'user_email': transaction.email,
                            'transaction_currency': transaction.currency_name
                        })
                
                return json({
                    'message': 'Deposit Transaction data fetched successfully', 
                    'deposit_transactions': combined_data,
                    'success': True,
                    'total_row_count': total_deposit_row_count
                    }, 200)

        except Exception as e:
            return json({'error': f'{str(e)}'}, 400)
        



# View details of a Deposit Transaction
class DepositTransactionDetailController(APIController):

    @classmethod
    def route(cls) -> str:
        return '/api/v2/admin/deposit/transaction/detail/{transaction_id}'
    
    @classmethod
    def class_name(cls) -> str:
        return 'Deposit Transaction Details'
    

    @auth('userauth')
    @get()
    async def get_deposit_details(self, request: Request, transaction_id: int):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                AdminID       = user_identity.claims.get('user_id') if user_identity else None

                # Admin Authentication
                admin_obj = await session.execute(select(Users).where(Users.id == AdminID))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data or not admin_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 401)
                # Admin Authentication ends

                combined_data = []

                # Get the transaction
                transaction_id_obj     = await session.execute(select(
                    DepositTransaction.id,
                    DepositTransaction.transaction_id,
                    DepositTransaction.created_At,
                    DepositTransaction.amount,
                    DepositTransaction.transaction_fee,
                    DepositTransaction.payout_amount,
                    DepositTransaction.status,
                    DepositTransaction.payment_mode,
                    DepositTransaction.is_completed,
                    DepositTransaction.selected_wallet,
                    DepositTransaction.currency,

                    Users.full_name,
                    Users.email,
                    Currency.name.label('currency_name')
                    ).join(
                        Users,  Users.id == DepositTransaction.user_id
                    ).join(
                        Currency, Currency.id == DepositTransaction.currency
                    ).where(
                        DepositTransaction.id == transaction_id
                    ))
                
                transaction_id_details = transaction_id_obj.first()

                # Currency related to transaction
                currency_obj = await session.execute(select(Currency).where(
                    Currency.id == transaction_id_details.currency
                    ))
                currency = currency_obj.scalar()
                
                deposit_currency            = currency.name
                selected_wallet             = transaction_id_details.selected_wallet
                deposit_amount              = transaction_id_details.amount

                # Get the selected wallet
                deposit_selected_wallet = await session.execute(select(Wallet).where(
                    Wallet.id == selected_wallet
                ))
                deposit_selected_wallet_data = deposit_selected_wallet.scalar()

                # Get the currency of the Wallet
                selected_wallet_currency      = await session.execute(select(Currency).where(
                    Currency.id == deposit_selected_wallet_data.currency_id
                    ))
                selected_wallet_currency_data = selected_wallet_currency.scalar()

                # Call API for currency Conversion
                try:
                    url = f"{currency_converter_api}/convert?from={deposit_currency}&to={selected_wallet_currency_data.name}&amount={deposit_amount}"
                    headers = {
                        'X-RapidAPI-Key': f"{RAPID_API_KEY}",
                        'X-RapidAPI-Host': f"{RAPID_API_HOST}"
                    }
                    
                    async with AsyncClient() as client:
                        response = await client.get(url, headers=headers)

                        if response.status_code == 200:
                            api_data = response.json()

                        else:
                            return json({'msg': 'Error calling external API', 'error': response.text}, 400)
                        
                except Exception as e:
                    return json({'msg': 'Currency API Error', 'error': f'{str(e)}'}, 400)

                converted_amount = api_data['result'] if 'result' in api_data else None

                if not converted_amount:
                    return json({'msg': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)
                
                combined_data.append({
                    'id': transaction_id_details.id,
                    'transaction_id': transaction_id_details.transaction_id,
                    'created_At': transaction_id_details.created_At,
                    'amount': transaction_id_details.amount,
                    'transaction_fee': transaction_id_details.transaction_fee,
                    'payout_amount': transaction_id_details.payout_amount,
                    'status': transaction_id_details.status,
                    'payment_mode': transaction_id_details.payment_mode,
                    'is_completed': transaction_id_details.is_completed,
                    'user_name': transaction_id_details.full_name,
                    'user_email': transaction_id_details.email,
                    'transaction_currency': transaction_id_details.currency_name,
                    'converted_amount': converted_amount,
                    'converted_currency': selected_wallet_currency_data.name
                })

                return json({"msg": "Transaction details fetched", "deposite_data": combined_data}, 200)
                
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        



## Update Deposit Transaction by Admin
class UpdateDepositController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Update Deposit Transaction'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v4/admin/update/deposit/transaction/'
    
    @auth('userauth')
    @put()
    async def update_deposit(self, request: Request, input: FromJSON[UpdateTransactionSchema]):
        try:
            async with AsyncSession(async_engine) as session:
                data = input.value

                user_identity = request.identity
                AdminID       = user_identity.claims.get("user_id") if user_identity else None

                user_obj = await session.execute(select(Users).where(Users.id == AdminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'msg': 'Admin authorization Failed'}, 401)
                #Admin authentication ends

                # Get the deposit transaction
                transaction_obj = await session.execute(select(DepositTransaction).where(
                    DepositTransaction.id == data.transaction_id
                    ))
                transaction_data = transaction_obj.scalar()

                if not transaction_data:
                    return pretty_json({'message': 'Requested transaction not available'}, 404)
                
                # If the transaction already approved
                if transaction_data.is_completed:
                    return json({'message': 'Transaction is completed'}, 400)
                
                
                # For Approved status
                if data.status == 'Approved':
                    user_id         = transaction_data.user_id
                    currency_id     = transaction_data.currency
                    selected_wallet = transaction_data.selected_wallet

                    # Selected wallet
                    sender_wallet     = await session.execute(select(Wallet).where(
                        Wallet.id == selected_wallet
                        ))
                    sender_wallet_obj = sender_wallet.scalar()

                    if not sender_wallet:
                        return json({"message": "Sender donot have a selected wallet"}, status=404)
                    
                    # Selected wallet Currency
                    selected_wallet_currency_name = sender_wallet_obj.currency

                    # get Currency ID
                    currency_to_convert = await session.execute(select(Currency).where(
                        Currency.id == currency_id
                        ))
                    currency_to_convert_obj = currency_to_convert.scalar()

                    if not currency_to_convert_obj:
                        return json({"msg": "Currency Not found"}, status=404)
                    
                    currency_to_convert_name = currency_to_convert_obj.name

                    try:
                        url = f"{currency_converter_api}/convert?from={currency_to_convert_name}&to={selected_wallet_currency_name}&amount={transaction_data.amount}"
                        headers = {
                        'X-RapidAPI-Key': f"{RAPID_API_KEY}",
                        'X-RapidAPI-Host': f"{RAPID_API_HOST}"
                    }
                        
                        async with AsyncClient() as client:
                            response = await client.get(url, headers=headers)
                            # print('APi Response', response)

                            if response.status_code == 200:
                                api_data = response.json()
                                # print('api data', api_data)

                            else:
                                return json({'message': 'Error calling external API', 'error': response.text}, 400)
                            
                    except Exception as e:
                        return json({'message': 'Currency API Error', 'error': f'{str(e)}'}, 400)

                    converted_amount = api_data['result'] if 'result' in api_data else None

                    if not converted_amount:
                        return json({'message': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)

                    sender_wallet_obj.balance += converted_amount

                    session.add(sender_wallet_obj)
                    # await session.commit()

                    transaction_data.status            = 'Approved'
                    transaction_data.is_completed      = True
                    transaction_data.payout_amount     = converted_amount
                    transaction_data.credited_currency = selected_wallet_currency_name
                    transaction_data.credited_amount   = converted_amount


                    session.add(transaction_data)
                    await session.commit()
                    await session.refresh(transaction_data)
                    await session.refresh(sender_wallet_obj)

                    return pretty_json({
                        'msg': 'Deposit Transaction Updated Successfully', 
                        'is_completed': True
                        }, 200)
                else:
                    transaction_data.status = data.status

                    session.add(transaction_data)
                    await session.commit()
                    await session.refresh(transaction_data)

                    return pretty_json({'msg': 'Transaction Updated Successfully', 
                                        'is_completed': False
                                        }, 200)
                
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)




### Filter FIAT Filter 
class AdminFiletrFIATDepositController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Filter FIAT Deposit Controller'
    

    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/admin/filter/fiat/deposit/'
    

    @auth('userauth')
    @post()
    async def Filter_Fiat_Deposit(self, request: Request, schema: AdminFilterFIATDeposits):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                AdminID       = user_identity.claims.get("user_id") if user_identity else None

                user_obj = await session.execute(select(Users).where(Users.id == AdminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'msg': 'Admin authorization Failed'}, 401)
                #Admin authentication ends

                ## Get payload data
                dateTime   = schema.date_time
                user_email = schema.email
                status     = schema.status
                currency   = schema.currency

                conditions    = []
                combined_data = []

                ## Get The user from Mail
                if user_email:
                    fiat_user_obj = await session.execute(select(Users).where(
                        Users.email.ilike(f"{user_email}%")
                    ))
                    fiat_user = fiat_user_obj.scalar()

                    if not fiat_user:
                        return json({'message': 'Invalid Email'}, 400)
                
                ## Select the columns
                stmt  = select(
                        DepositTransaction.id,
                        DepositTransaction.transaction_id,
                        DepositTransaction.created_At,
                        DepositTransaction.amount,
                        DepositTransaction.transaction_fee,
                        DepositTransaction.payout_amount,
                        DepositTransaction.status,
                        DepositTransaction.payment_mode,
                        DepositTransaction.is_completed,

                        Users.full_name,
                        Users.email,
                        Currency.name.label('currency_name')
                    ).join(
                        Users,  Users.id == DepositTransaction.user_id
                    ).join(
                        Currency, Currency.id == DepositTransaction.currency
                    ).order_by(
                        desc(DepositTransaction.id)
                    )
                
                ## Filter email wise
                if user_email:
                    conditions.append(
                        DepositTransaction.user_id == fiat_user.id
                    )

                ## Filter status wise
                if status:
                    conditions.append(
                        DepositTransaction.status.ilike(f"{status}%")
                    )

                ## Filter date time wise
                if dateTime:
                    start_date, end_date = get_date_range(dateTime)

                    conditions.append(
                        and_(
                            DepositTransaction.created_At <= end_date,
                            DepositTransaction.created_At >= start_date
                        )
                    )

                ## Filter amount wise
                if currency:
                    filter_currency_obj = await session.execute(select(Currency).where(
                        Currency.name.ilike(f"{currency}%")
                    ))
                    filter_currency = filter_currency_obj.scalar()

                    conditions.append(
                        DepositTransaction.currency == filter_currency.id
                    )
                
                ## if filterd data available
                if conditions:
                    statement = stmt.where(and_(*conditions))

                    fiat_deposit_transactions_obj = await session.execute(statement)
                    fiat_deposit_transactions     = fiat_deposit_transactions_obj.fetchall()

                    if not fiat_deposit_transactions:
                        return json({'message': 'No data found'}, 404)
                
                else:
                    return json({'message': 'No data found'}, 404)
                
                ## Get all data in combined_data
                for transaction in fiat_deposit_transactions:

                    combined_data.append({
                        'id': transaction.id,
                        'transaction_id': transaction.transaction_id,
                        'created_At': transaction.created_At,
                        'amount': transaction.amount,
                        'transaction_fee': transaction.transaction_fee,
                        'payout_amount': transaction.payout_amount,
                        'status': transaction.status,
                        'payment_mode': transaction.payment_mode,
                        'is_completed': transaction.is_completed,
                        'user_name': transaction.full_name,
                        'user_email': transaction.email,
                        'transaction_currency': transaction.currency_name
                    })

                return json({
                    'message': 'Deposit Transaction data fetched successfully', 
                    'filter_deposit_transactions': combined_data,
                    'success': True
                }, 200)
            
        except Exception as e:
            return json({
                'error': 'Server Error', 
                'message': f'{str(e)}'
                }, 500)
        



## Export Deposit Transaction
class AdminExportDepositTransactionsController(APIController):

    @classmethod
    def class_name(cls):
        return 'Export Deposit Transactions'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/admin/export/deposit/transactions/'
    
    ### Export Deposit Transactions
    @auth('userauth')
    @get()
    async def export_depositTransaction(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                AdminID       = user_identity.claims.get('user_id')

                user_obj = await session.execute(select(Users).where(Users.id == AdminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'msg': 'Admin authorization Failed'}, 401)
                #Admin authentication ends

                stmt  = select(
                    DepositTransaction.transaction_id,
                    DepositTransaction.created_At,
                    DepositTransaction.amount,
                    DepositTransaction.transaction_fee,
                    DepositTransaction.payout_amount,
                    DepositTransaction.status,
                    DepositTransaction.payment_mode,
                    DepositTransaction.credited_amount,
                    DepositTransaction.credited_currency,

                    Users.full_name,
                    Users.email,
                    Currency.name.label('currency_name')

                    ).join(
                        Users,  Users.id == DepositTransaction.user_id
                    ).join(
                        Currency, Currency.id == DepositTransaction.currency
                    ).order_by(
                        desc(DepositTransaction.id)
                    )
                
                #Get all transaction Data
                get_all_transaction     = await session.execute(stmt)
                get_all_transaction_obj = get_all_transaction.all()

                combined_data = []

                if not get_all_transaction_obj:
                    return json({'msg': "No Transaction available"}, 404)
                
                for transaction in get_all_transaction_obj:
                    combined_data.append({
                        'transaction_id': transaction.transaction_id,
                        'created_At': transaction.created_At,
                        'amount': transaction.amount,
                        'transaction_fee': transaction.transaction_fee,
                        'status': transaction.status,
                        'payment_mode': transaction.payment_mode,
                        'user_name': transaction.full_name,
                        'user_email': transaction.email,
                        'transaction_currency': transaction.currency_name,
                        'credited_amount': transaction.credited_amount,
                        'credited_currency': transaction.credited_currency
                    })

                return json({
                    'message': 'Deposit Transaction data fetched successfully', 
                    'export_deposit_transactions': combined_data,
                    'success': True
                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)