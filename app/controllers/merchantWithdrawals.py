from blacksheep import Request, json
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from app.controllers.controllers import get, post
from database.db import AsyncSession, async_engine
from Models.models import MerchantBankAccount, Currency, Users
from Models.models3 import MerchantWithdrawals
from Models.models2 import MerchantAccountBalance
from Models.PG.schema import CreateMerchantWithdrawlSchma
from sqlmodel import select, and_, desc, alias




# Merchant Withdrawals
class MerchantWithdrawalController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Withdrawal'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v3/merchant/withdrawal/'
    
    # Create new Withdrawal Request
    @auth('userauth')
    @post()
    async def create_merchantWithdrawal(self, request: Request, schema: CreateMerchantWithdrawlSchma):
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate user
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                # Payload data
                merchantBank         = schema.bank_id  # To be deposited bank
                merchantBankCurrency = schema.bank_currency_id # To be deposited Currency
                accountCurrency      = schema.account_currency # From Account Balance currency
                withdrawalAmount     = schema.withdrawal_amount  # Withdrawal amount


                # Check the merchant bank account is exist and active or not
                merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                    and_(MerchantBankAccount.id         == merchantBank,
                          MerchantBankAccount.is_active == True,
                          MerchantBankAccount.currency  == merchantBankCurrency
                         )
                ))
                merchant_bank_account = merchant_bank_account_obj.scalar()

                if not merchant_bank_account:
                    return json({'error': 'Bank account not active'}, 400)
                
                # If withdrawal amount is 0 or less than 10
                if withdrawalAmount == 0 or withdrawalAmount < 10:
                    return json({'error': 'Amount should be greater than 10'}, 400)
                
                # Get the merchant Account Balance
                merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                    MerchantAccountBalance.currency == accountCurrency
                ))
                merchant_account_balance_ = merchant_account_balance_obj.scalar()

                if not merchant_account_balance_:
                    return json({'error': 'Do not have any active account in the currency'}, 400)
                
                # Withdrawal balance is lesser than Account balance or not
                merchant_account_balance = merchant_account_balance_.amount

                if withdrawalAmount >= merchant_account_balance:
                    return json({'error': 'Donot have sufficient balance in Account'}, 400)
                
                # Currency
                account_currency_obj = await session.execute(select(Currency).where(
                    Currency.name == accountCurrency
                ))
                account_currency = account_currency_obj.scalar()


                # Create a Withdrawal Request
                merchant_withdrawal_request = MerchantWithdrawals(
                    merchant_id      = user_id,
                    bank_id          = merchant_bank_account.id,
                    amount           = withdrawalAmount,
                    bank_currency    = merchantBankCurrency,
                    currency         = account_currency.id,
                    is_active        = False
                )

                session.add(merchant_withdrawal_request)
                await session.commit()
                await session.refresh(merchant_withdrawal_request)

                return json({'success': True, 'message': 'Withdrawal request raised successfully'}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        
 
    # Get all the pending withdrawals
    @auth('userauth')
    @get()
    async def get_merchantWithdrawals(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate User
                user_identity = request.identity
                user_id = user_identity.claims.get('user_id') if user_identity else None

                combined_data = []

                # Get all the Withdrawal request raise by the merchant
                merchantWithdrawalRequests = await session.execute(select(MerchantWithdrawals).where(
                    MerchantWithdrawals.merchant_id == user_id
                ).order_by(desc(MerchantWithdrawals.id)))
                merchantWithdrawal = merchantWithdrawalRequests.scalars().all()

                if not merchantWithdrawal:
                    return json({'error': 'No withdrawal request found'}, 404)
                
                for withdrawals in merchantWithdrawal:
                    # Get the bank account linked to the merchant
                    merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                        MerchantBankAccount.id == withdrawals.bank_id
                    ))
                    merchant_bank_account = merchant_bank_account_obj.scalar()

                    # Get the withdrawal currency and Bank Currecy
                    merchant_withdrawal_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.currency
                    ))
                    merchant_withdrawal_currency = merchant_withdrawal_currency_obj.scalar()

                    # Get the merchant Bank Currency
                    merchant_bank_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.bank_currency
                    ))
                    merchant_bank_currency = merchant_bank_currency_obj.scalar()

                    # Get user Details
                    merchant_user_obj = await session.execute(select(Users).where(
                        Users.id == withdrawals.merchant_id
                    ))
                    merchant_user = merchant_user_obj.scalar()


                    combined_data.append({
                        'id': withdrawals.id,
                        'merchant_id': withdrawals.merchant_id,
                        'merchant_name': merchant_user.full_name,
                        'merchant_email': merchant_user.email,
                        'bank_account': merchant_bank_account.bank_name,
                        'bank_account_number': merchant_bank_account.acc_no,
                        'bankCurrency': merchant_bank_currency.name,
                        'withdrawalAmount': withdrawals.amount,
                        'withdrawalCurrency': merchant_withdrawal_currency.name,
                        'createdAt': withdrawals.createdAt,
                        'status':   withdrawals.status,
                        'is_active': withdrawals.is_active
                    })

                return json({'success': True, 'merchantWithdrawalRequests': combined_data}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        



# Merchant Pending Withdrawals
class MerchantPendingWithdrawalController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Pending Withdrawals'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v3/merchant/pg/pending/withdrawal/'
    
    # Create new Withdrawal Request
    @auth('userauth')
    @get()
    async def get_merchantPendingWithdrawals(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate user
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                combined_data = []

                # Get all the pending Withdrawal request raise by the merchant
                stmt = select(MerchantWithdrawals.id,
                              MerchantWithdrawals.bank_currency,
                              MerchantWithdrawals.merchant_id,
                              MerchantWithdrawals.amount,
                              MerchantWithdrawals.status,
                              MerchantWithdrawals.is_active,
                              MerchantWithdrawals.createdAt,

                              MerchantBankAccount.bank_name,
                              Currency.name
                              ).join(
                                  MerchantBankAccount, MerchantBankAccount.id == MerchantWithdrawals.bank_id
                              ).join(
                                  Currency, Currency.id == MerchantWithdrawals.currency
                              )
                merchantWithdrawalRequests = await session.execute(stmt.where(
                    and_(
                        MerchantWithdrawals.merchant_id == user_id,
                         MerchantWithdrawals.status == 'Pending'
                         )
                ).order_by(desc(MerchantWithdrawals.id)))

                merchantWithdrawal = merchantWithdrawalRequests.all()

                if not merchantWithdrawal:
                    return json({'message': 'No withdrawal request found'}, 404)
                
                for withdrawals in merchantWithdrawal:

                    combined_data.append({
                        'id': withdrawals.id,
                        'merchant_id': withdrawals.merchant_id,
                        'withdrawalAmount': withdrawals.amount,
                        'withdrawalCurrency': withdrawals.name,
                        'createdAt': withdrawals.createdAt,
                        'status':   withdrawals.status,
                        'is_active': withdrawals.is_active
                    })

                return json({'success': True, 'merchantPendingWithdrawals': combined_data}, 200)
                
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)