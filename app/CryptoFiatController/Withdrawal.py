from app.controllers.controllers import get, post
from blacksheep import json, Request
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_, desc, func
from Models.PG.schema import FiatUserWithdrawalSchema
from Models.models4 import FiatWithdrawalTransaction
from Models.models import Wallet, Currency, Users
import uuid



## Raise Withdrawal Request by User
class UserFiatWithdrawalController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'User Fiat Withdrawal'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/user/fiat/withdrawal/'
    
    # Raise Withdrawal Request by User
    @auth('userauth')
    @post()
    async def withdrawal_fiat_amount(self, request: Request, schema: FiatUserWithdrawalSchema):
        """
            Raise Withdrawal Request By Fiat User
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                # Get The payload data
                walletCurrency     = schema.wallet_currency
                withdrawalCurrency = schema.withdrawalCurrency
                withdrawalAmount   = float(schema.withdrawalAmount)
                withdrawalFee      = float(schema.fee)

                # Get wallet Currency
                wallet_currency_obj = await session.execute(select(Currency).where(
                    Currency.name == walletCurrency
                ))
                wallet_currency_ = wallet_currency_obj.scalar()

                if not wallet_currency_:
                    return json({'message': 'Invalid Wallet Currency'}, 400)

                # Get the wall                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              et of the user
                user_wallet_obj = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.user_id == user_id,
                        Wallet.currency_id == wallet_currency_.id
                    )
                ))
                user_wallet = user_wallet_obj.scalar()

                if not user_wallet:
                    return json({'message': 'User wallet does not exists'}, 400)
                
                # Account balance check
                if withdrawalAmount > user_wallet.balance:
                    return json({'message': 'Do not have Sufficient balance in Wallet'}, 400)
                
                # Get the withdrawal Currency
                withdrawal_currency_obj = await session.execute(select(Currency).where(
                    Currency.name == withdrawalCurrency
                ))
                withdrawal_currency_ = withdrawal_currency_obj.scalar()

                if not withdrawal_currency_:
                    return json({'message': 'Invalid withdrawal Currency'}, 400)
                
                total_amt = withdrawalAmount + withdrawalFee

                # Create a Withdrawal Request
                withdrawal_request = FiatWithdrawalTransaction(
                    user_id             = user_id,
                    transaction_id      = str(uuid.uuid4()),
                    amount              = withdrawalAmount,
                    total_amount        = total_amt,
                    transaction_fee     = withdrawalFee,
                    wallet_currency     = wallet_currency_.id,
                    withdrawal_currency = withdrawal_currency_.id,
                    status              = 'Pending',
                    credit_currency     = withdrawal_currency_.name 
                )

                session.add(withdrawal_request)
                await session.commit()
                await session.refresh(withdrawal_request)

                return json({'success': True, 'message': 'Withdrawak Request Raised Successfully'}, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        

    @auth('userauth')
    @get()
    async def get_all_fiat_withdrawal(self, request: Request, limit: int = 10, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                combined_data = []

                # total_row_count_obj = await session.execute(select(func.count(FiatWithdrawalTransaction.id)))
                # total_row_count     = total_row_count_obj.scalar()


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
                    FiatWithdrawalTransaction.credit_amount,
                    FiatWithdrawalTransaction.credit_currency,
                    FiatWithdrawalTransaction.is_completed,
                    FiatWithdrawalTransaction.created_At,

                    Currency.name.label('wallet_currency'),

                    Users.email.label('user_email')
                ).join(
                    Currency, Currency.id == FiatWithdrawalTransaction.wallet_currency
                ).join(
                    Users, Users.id == FiatWithdrawalTransaction.user_id
                ).where(
                    FiatWithdrawalTransaction.user_id == user_id
                )

                # Get the withdrdrawlas
                withdrawals_obj = await session.execute(stmt)
                all_fiat_withdrawals = withdrawals_obj.all()

                for withdrawals in all_fiat_withdrawals:

                    withdrawal_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.withdrawal_currency
                    ))
                    withdrawal_currency = withdrawal_currency_obj.scalar()

                    combined_data.append({
                        'id': withdrawals.id,
                        'user_id': withdrawals.user_id,
                        'user_email': withdrawals.user_email,
                        'transaction_id': withdrawals.transaction_id,
                        'amount': withdrawals.amount,
                        'total_amount': withdrawals.total_amount,
                        'transaction_fee': withdrawals.transaction_fee,
                        'withdrawal_currency': withdrawal_currency.name,
                        'wallet_currency': withdrawals.wallet_currency,
                        'status': withdrawals.status,
                        'credit_amount': withdrawals.credit_amount,
                        'credit_currency': withdrawals.credit_currency,
                        'is_completed': withdrawals.is_completed,
                        'created_At': withdrawals.created_At
                    })

                return json({
                            'success': True,
                            'all_fiat_withdrawals': combined_data
                        }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)