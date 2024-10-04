from app.controllers.controllers import get, put, post
from blacksheep import json, Request
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_, desc, func
from Models.models import Users, Currency, Wallet
from Models.models4 import FiatWithdrawalTransaction
from Models.Admin.FiatWithdrawal.schema import UpdateFiatWithdrawalsSchema
from httpx import AsyncClient
from decouple import config




currency_converter_api = config('CURRENCY_CONVERTER_API')
RAPID_API_KEY          = config('RAPID_API_KEY')
RAPID_API_HOST         = config('RAPID_API_HOST')



## FIAT Withdrawal controller
class AdminAllWithdrawalTransactionController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return "All Withdrawals"
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/admin/fiat/withdrawals/'
    

    # Get all Fiat withdrawal requests
    @auth('userauth')
    @get()
    async def get_all_user_withdrawals(self, request: Request, limit: int = 10, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                combined_data = []

                #Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                        Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Admin authentication Failed'}, 401)
                # Admin authentication ends

                row_statement = select(func.count(FiatWithdrawalTransaction.id))
                exe_row_statement = await session.execute(row_statement)
                withdrawal_rows = exe_row_statement.scalar()

                total_withdrawal_rows = withdrawal_rows / limit

                # Select the withdrawal table
                stmt = select(
                    FiatWithdrawalTransaction.id,
                    FiatWithdrawalTransaction.user_id,
                    FiatWithdrawalTransaction.transaction_id,
                    FiatWithdrawalTransaction.amount,
                    FiatWithdrawalTransaction.total_amount,
                    FiatWithdrawalTransaction.transaction_fee,
                    FiatWithdrawalTransaction.withdrawal_currency,
                    FiatWithdrawalTransaction.status,
                    FiatWithdrawalTransaction.debit_amount,
                    FiatWithdrawalTransaction.debit_currency,
                    FiatWithdrawalTransaction.is_completed,
                    FiatWithdrawalTransaction.created_At,

                    Currency.name.label('wallet_currency'),

                    Users.email.label('user_email'),
                    Users.full_name.label('user_name')
                ).join(
                    Currency, Currency.id == FiatWithdrawalTransaction.wallet_currency
                ).join(
                    Users, Users.id == FiatWithdrawalTransaction.user_id
                ).order_by(
                    desc(FiatWithdrawalTransaction.id)
                )

                # Get the withdrdrawlas
                withdrawals_obj      = await session.execute(stmt)
                all_fiat_withdrawals = withdrawals_obj.all()

                if not all_fiat_withdrawals:
                    return json({'message': 'No Withdrawal found'}, 404)
                
                # Store all the data inside a combined_data list
                for withdrawals in all_fiat_withdrawals:

                    withdrawal_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.withdrawal_currency
                    ))
                    withdrawal_currency = withdrawal_currency_obj.scalar()

                    combined_data.append({
                        'id': withdrawals.id,
                        'user_id': withdrawals.user_id,
                        'user_email': withdrawals.user_email,
                        'user_name': withdrawals.user_name,
                        'transaction_id': withdrawals.transaction_id,
                        'amount': withdrawals.amount,
                        'total_amount': withdrawals.total_amount,
                        'transaction_fee': withdrawals.transaction_fee,
                        'withdrawal_currency': withdrawal_currency.name,
                        'wallet_currency': withdrawals.wallet_currency,
                        'status': withdrawals.status,
                        'credit_amount': withdrawals.debit_amount,
                        'credit_currency': withdrawals.debit_currency,
                        'is_completed': withdrawals.is_completed,
                        'created_At': withdrawals.created_At
                    })

                return json({
                        'success': True,
                        'all_admin_fiat_withdrawals': combined_data,
                        'total_row_count': total_withdrawal_rows
                    }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        

    # Get FIAT Withdrawal Details
    @auth('userauth')
    @post()
    async def get__fiat_withdrawals(self, request: Request, id: int):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                combined_data = []
                withdrawal_id = id

                # Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                        Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Admin authentication Failed'}, 401)
                # Admin authentication ends

                # Select the withdrawal table
                stmt = select(
                    FiatWithdrawalTransaction.id,
                    FiatWithdrawalTransaction.user_id,
                    FiatWithdrawalTransaction.transaction_id,
                    FiatWithdrawalTransaction.amount,
                    FiatWithdrawalTransaction.total_amount,
                    FiatWithdrawalTransaction.transaction_fee,
                    FiatWithdrawalTransaction.withdrawal_currency,
                    FiatWithdrawalTransaction.wallet_currency,
                    FiatWithdrawalTransaction.status,
                    FiatWithdrawalTransaction.debit_amount,
                    FiatWithdrawalTransaction.debit_currency,
                    FiatWithdrawalTransaction.is_completed,
                    FiatWithdrawalTransaction.created_At,

                    Currency.name.label('wallet_currency_name'),

                    Users.email.label('user_email'),
                    Users.full_name.label('user_name')
                ).join(
                    Currency, Currency.id == FiatWithdrawalTransaction.wallet_currency
                ).join(
                    Users, Users.id == FiatWithdrawalTransaction.user_id
                ).where(
                    FiatWithdrawalTransaction.id == withdrawal_id
                )

                # Get the withdrdrawlas
                withdrawal_obj  = await session.execute(stmt)
                fiat_withdrawal = withdrawal_obj.first()

                # Get the wallet of the user
                user_wallet_obj = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.currency_id == fiat_withdrawal.wallet_currency,
                        Wallet.user_id     == fiat_withdrawal.user_id
                    )
                ))
                user_wallet = user_wallet_obj.scalar()

                if not user_wallet:
                    return json({'message': 'User do not have any existing wallet'}, 400)
                
                # From Currency 
                from_currency_obj = await session.execute(select(Currency).where(
                    Currency.id == fiat_withdrawal.wallet_currency
                ))
                from_currency = from_currency_obj.scalar()

                # To Currency
                to_currency_obj = await session.execute(select(Currency).where(
                    Currency.id == fiat_withdrawal.withdrawal_currency
                ))
                to_currency = to_currency_obj.scalar()


                # Call API for currency Conversion
                try:
                    url = f"{currency_converter_api}/convert?from={from_currency.name}&to={to_currency.name}&amount={fiat_withdrawal.amount}"
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
                
                # Withdrawal Currency
                withdrawal_currency_obj = await session.execute(select(Currency).where(
                    Currency.id == fiat_withdrawal.withdrawal_currency
                ))
                withdrawal_currency = withdrawal_currency_obj.scalar()

                combined_data.append({
                    'id': fiat_withdrawal.id,
                    'user_name': fiat_withdrawal.user_name,
                    'user_email': fiat_withdrawal.user_email,
                    'wallet_currency': fiat_withdrawal.wallet_currency_name,
                    'wallet_balance': user_wallet.balance,
                    'transaction_id': fiat_withdrawal.transaction_id,
                    'withdrawal_amount': fiat_withdrawal.amount,
                    'withdrawal_currency': withdrawal_currency.name,
                    'withdrawal_fee': fiat_withdrawal.transaction_fee,
                    'total_amount': fiat_withdrawal.total_amount,
                    'status': fiat_withdrawal.status,
                    'debit_amount': converted_amount,
                    'debit_currency': withdrawal_currency.name,
                    'created_At': fiat_withdrawal.created_At,
                })

                return json({
                    'success': True,
                    'withdrawal_data': combined_data
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        

    # Update FIAT Withdrawal
    @auth('userauth')
    @put()
    async def update_fiat_withdrawals(self, request: Request, schema: UpdateFiatWithdrawalsSchema):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                # Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                        Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Admin authentication Failed'}, 401)
                # Admin authentication ends

                # Get the payload data
                withdrawal_id    = schema.withdrawal_id
                converted_amount = schema.converted_amount
                status           = schema.status

                # Get the withdrawal object
                user_fiat_withdrawal_obj = await session.execute(select(FiatWithdrawalTransaction).where(
                    FiatWithdrawalTransaction.id == withdrawal_id
                ))
                user_fiat_withdrawal = user_fiat_withdrawal_obj.scalar()

                if user_fiat_withdrawal.is_completed:
                    return json({'message': 'Transaction Already Approved can not perform this action'}, 400)

                # Get the wallet of the user
                user_wallet_obj = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.currency_id == user_fiat_withdrawal.wallet_currency,
                        Wallet.user_id     == user_fiat_withdrawal.user_id
                    )
                ))
                user_wallet = user_wallet_obj.scalar()

                if not user_wallet:
                    return json({'message': 'User do not have any existing wallet'}, 400)
                

                ## Wallet balance validation
                if user_wallet.balance < user_fiat_withdrawal.amount:
                    return json({'message': 'Do not have sufficient balance in wallet'}, 400)
                
                if status == 'Approved':
                    total_withdrawal_amount = user_fiat_withdrawal.amount + user_fiat_withdrawal.transaction_fee

                    # Deduct the amount
                    user_wallet.balance -= total_withdrawal_amount

                    # user Wallet currency Name
                    wallet_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == user_wallet.currency_id
                    ))
                    wallet_currency = wallet_currency_obj.scalar()

                    # user Withdrawal currency Name
                    withdrawal_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == user_fiat_withdrawal.withdrawal_currency
                    ))
                    withdrawal_currency = withdrawal_currency_obj.scalar()

                    user_fiat_withdrawal.debit_amount    = float(total_withdrawal_amount)
                    user_fiat_withdrawal.debit_currency  = wallet_currency.name
                    user_fiat_withdrawal.credit_amount   = float(converted_amount)
                    user_fiat_withdrawal.credit_currency = withdrawal_currency.name
                    user_fiat_withdrawal.status          = 'Approved'
                    user_fiat_withdrawal.is_completed    = True

                    session.add(user_wallet)
                    session.add(user_fiat_withdrawal)
                    await session.commit()
                    await session.refresh(user_wallet)
                    await session.refresh(user_fiat_withdrawal)

                    return json({
                        'success': True,
                        'message': 'Updated Successfully'
                    }, 200)

                else:
                    user_fiat_withdrawal.status       = status
                    user_fiat_withdrawal.is_completed = False

                    session.add(user_fiat_withdrawal)
                    await session.commit()
                    await session.refresh(user_fiat_withdrawal)

                    return json({
                        'success': True,
                        'message': 'Updated Successfully'
                    }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)

