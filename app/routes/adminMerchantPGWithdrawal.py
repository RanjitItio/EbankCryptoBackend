from blacksheep import Request, json, get, put
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models3 import MerchantWithdrawals
from Models.models import MerchantBankAccount, Users, Currency
from Models.models2 import MerchantAccountBalance
from Models.Admin.PG.schema import AdminWithdrawalUpdateSchema
from sqlmodel import select, and_, or_, cast, Date, Time
from datetime import datetime



# Get all merchant withdrawals
@auth('userauth')
@get('/api/v4/admin/merchant/pg/withdrawals/')
async def AdminMerchantWithdrawalRequests(request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate Admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            admin_user = admin_user_obj.scalar()

            is_admin_user = admin_user.is_admin

            if not is_admin_user:
                return json({'error': 'Admin authentication failed'}, 401)
            # Admin authentication Ends

            # Get all the merchant withdrawals
            stmt = select(MerchantWithdrawals.id, 
                          MerchantWithdrawals.merchant_id,
                          MerchantWithdrawals.amount,
                          MerchantWithdrawals.createdAt,
                          MerchantWithdrawals.currency,
                          MerchantWithdrawals.bank_currency,
                          MerchantWithdrawals.status,
                          MerchantWithdrawals.is_active,
                          MerchantBankAccount.bank_name,
                          Users.full_name,
                          Users.email,
                          ).join(
                               Users, Users.id == MerchantWithdrawals.merchant_id
                          ).join(
                               MerchantBankAccount, MerchantBankAccount.id == MerchantWithdrawals.bank_id
                          )
            merchant_withdrawals_object = await session.execute(stmt)
            merchant_withdrawals        = merchant_withdrawals_object.all()


            if not merchant_withdrawals:
                 return json({'error': 'No withdrawal request found'}, 404)
            

            for withdrawals in merchant_withdrawals:
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

                    # Get merchant account balance
                    merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                         and_(MerchantAccountBalance.merchant_id == withdrawals.merchant_id,
                              MerchantAccountBalance.currency    == merchant_withdrawal_currency.name
                              )
                    ))
                    merchant_account_balance_ = merchant_account_balance_obj.scalar()

                    combined_data.append({
                        'id': withdrawals.id,
                        'merchant_id': withdrawals.merchant_id,
                        'merchant_name': withdrawals.full_name,
                        'merchant_email': withdrawals.email,
                        'bank_account': withdrawals.bank_name,
                        'bankCurrency': merchant_bank_currency.name,
                        'withdrawalAmount': withdrawals.amount,
                        'withdrawalCurrency': merchant_withdrawal_currency.name,
                        'createdAt': withdrawals.createdAt,
                        'status':   withdrawals.status,
                        'is_active': withdrawals.is_active,
                        'account_balance': merchant_account_balance_.amount,
                        'account_currency': merchant_account_balance_.currency
                    })

            return json({'success': True, 'AdminMerchantWithdrawalRequests': combined_data}, 200)

            
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



# Update Merchant withdrawals by Admin
@auth('userauth')
@put('/api/v4/admin/merchant/withdrawal/update/')
async def MerchantWithdrawalTransactionUpdate(request: Request, schema: AdminWithdrawalUpdateSchema):
     try:
          async with AsyncSession(async_engine) as session:
               # Admin Authentication
               user_identity = request.identity
               user_id       = user_identity.claims.get('user_id') if user_identity else None

               admin_user_obj = await session.execute(select(Users).where(
                    Users.id == user_id
               ))
               admin_user = admin_user_obj.scalar()

               if not admin_user.is_admin:
                    return json({'error': 'Admin authentication failed'}, 401)
               # Admin authentication ends here

               # Payload data
               status        = schema.status
               withdrawal_id = schema.withdrawal_id

               # Get the merchant withdrawal transaction
               merchant_withdrawals_obj = await session.execute(select(MerchantWithdrawals).where(
                    MerchantWithdrawals.id == withdrawal_id
               ))
               merchant_withdrawals = merchant_withdrawals_obj.scalar()

               if not merchant_withdrawals:
                    return json({'message': 'No Withdrawal request found with given information'}, 404)
               
               # Get the currency
               currency_obj = await session.execute(select(Currency).where(
                    Currency.id == merchant_withdrawals.currency
               ))
               currency = currency_obj.scalar()

               # Get merchant account balance
               merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                    and_(MerchantAccountBalance.merchant_id == merchant_withdrawals.merchant_id,
                         MerchantAccountBalance.currency    == currency.name
                         )
               ))
               merchant_account_balance = merchant_account_balance_obj.scalar()

               account_balance_amount = merchant_account_balance.amount

               # If available balance is less than withdrawal balance
               if account_balance_amount < merchant_withdrawals.amount:
                    return json({'message': 'Insufficient balance to withdrawal'}, 400)
               
               # Update withdrawal status
               if status == 'Approved':
                    merchant_withdrawals.status    = status
                    merchant_withdrawals.is_active = True
               else:
                    merchant_withdrawals.status = status

               session.add(merchant_withdrawals)
               await session.commit()
               await session.refresh(merchant_withdrawals)

               return json({'success': True, 'message': 'Updated Successfully'}, 200)

     except Exception as e:
          return json({'error':'Server Error', 'message': f'{str(e)}'}, 500)
     


# Search Withdrawal transactions by Admin
@auth('userauth')
@get('/api/v4/admin/merchant/withdrawal/search/')
async def MerchantWithdrawalTransactionSearch(request: Request, query: str):
     try:
          async with AsyncSession(async_engine) as session:
               # Admin Authentication
               user_identity = request.identity
               user_id       = user_identity.claims.get('user_id') if user_identity else None

               admin_user_obj = await session.execute(select(Users).where(
                    Users.id == user_id
               ))
               admin_user = admin_user_obj.scalar()

               if not admin_user.is_admin:
                    return json({'error': 'Admin authentication failed'}, 401)
               # Admin authentication ends here

               query_date = None
               query_time = None

               try:
                    query_as_float = float(query)  # If query is a number, try to convert
               except ValueError:
                    query_as_float = None

               try:
                    query_date = datetime.strptime(query, "%Y-%m-%d").date()
               except ValueError:
                    pass

               try:
                    query_time = datetime.strptime(query, "%H:%M:%S.%f").time()
               except ValueError:
                    pass

               # Search user full name
               user_full_name_obj = await session.execute(
                    select(Users).where(Users.full_name == query)
               )
               user_full_name = user_full_name_obj.scalars().all()

               # Search User Email
               user_email_obj = await session.execute(
                    select(Users).where(Users.email == query)
                    )
               user_email = user_email_obj.scalar()

               # Search Currency wise
               currency_obj = await session.execute(
                    select(Currency).where(Currency.name == query)
               )
               currency = currency_obj.scalar()

               # Search amount wise
               withdrawal_amount_obj = await session.execute(
                    select(MerchantWithdrawals).where(
                         MerchantWithdrawals.amount == query_as_float
                    ) if query_as_float is not None else select(MerchantWithdrawals).where(
                         MerchantWithdrawals.amount == 0.00
                    )
               )
               withdrawal_amount = withdrawal_amount_obj.scalars().all()

               # Search status wise
               withdrawal_status_obj = await session.execute(
                    select(MerchantWithdrawals).where(MerchantWithdrawals.status == query)
                    )
               withdrawal_status = withdrawal_status_obj.scalars().all()


               stmt = select(MerchantWithdrawals.id, 
                          MerchantWithdrawals.merchant_id,
                          MerchantWithdrawals.amount,
                          MerchantWithdrawals.createdAt,
                          MerchantWithdrawals.currency,
                          MerchantWithdrawals.bank_currency,
                          MerchantWithdrawals.status,
                          MerchantWithdrawals.is_active,
                          MerchantBankAccount.bank_name,
                          Users.full_name,
                          Users.email,
                          ).join(
                               Users, Users.id == MerchantWithdrawals.merchant_id
                          ).join(
                               MerchantBankAccount, MerchantBankAccount.id == MerchantWithdrawals.bank_id
                          )
               
               conditions = []

               if user_full_name:
                    conditions.append(MerchantWithdrawals.merchant_id.in_([user.id for user in user_full_name]))

               elif user_email:
                    conditions.append(MerchantWithdrawals.merchant_id == user_email.id)

               elif currency:
                    conditions.append(MerchantWithdrawals.currency == currency.id)

               elif withdrawal_amount:
                    conditions.append(MerchantWithdrawals.amount.in_([wa.amount for wa in withdrawal_amount]))

               elif withdrawal_status:
                    conditions.append(MerchantWithdrawals.status.in_([ws.status for ws in withdrawal_status]))

               if query_date:
                    conditions.append(cast(MerchantWithdrawals.createdAt, Date) == query_date)

               if query_time:
                    conditions.append(cast(MerchantWithdrawals.createdAt, Time) == query_time)

               if conditions:
                    stmt = stmt.where(or_(*conditions))

               merchant_withdrawals_object = await session.execute(stmt)
               merchant_withdrawals = merchant_withdrawals_object.fetchall()

               merchant_withdrawals_data = []

               for mw in merchant_withdrawals:
                    # Currency Name
                    withdrawal_currency_obj = await session.execute(select(Currency).where(
                         Currency.id == mw.currency
                    ))
                    withdrawal_currency = withdrawal_currency_obj.scalar()

                    bank_currency_obj = await session.execute(select(Currency).where(
                         Currency.id == mw.bank_currency
                    ))
                    bank_currency = bank_currency_obj.scalar()

                    # Get merchant account balance
                    merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                         and_(MerchantAccountBalance.merchant_id == mw.merchant_id,
                              MerchantAccountBalance.currency    == withdrawal_currency.name
                              )
                    ))
                    merchant_account_balance_ = merchant_account_balance_obj.scalar()


                    merchant_withdrawals_data.append({
                         "id": mw.id,
                         "merchant_id": mw.merchant_id,
                         'merchant_name': mw.full_name,
                         'merchant_email': mw.email,
                         "createdAt": mw.createdAt.isoformat() if mw.createdAt else None,
                         "withdrawalAmount": mw.amount,
                         "withdrawalCurrency": withdrawal_currency.name,
                         "status": mw.status,
                         "is_active": mw.is_active,
                         "bank_account": mw.bank_name,
                         "bankCurrency": bank_currency.name,
                         "full_name": mw.full_name,
                         "email": mw.email,
                         'account_balance': merchant_account_balance_.amount,
                         'account_currency': merchant_account_balance_.currency
                    })
                    

               return json({'success': True, 'merchant_withdrawal_search': merchant_withdrawals_data}, 200)

     except Exception as e:
          return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)


     
# Export all merchant withdrawals by Admin
@auth('userauth')
@get('/api/v4/admin/merchant/pg/export/withdrawals/')
async def AdminMerchantExportWithdrawalRequests(request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate Admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            admin_user = admin_user_obj.scalar()

            is_admin_user = admin_user.is_admin

            if not is_admin_user:
                return json({'error': 'Admin authentication failed'}, 401)
            # Admin authentication Ends

            # Get all the merchant withdrawals
            stmt = select(MerchantWithdrawals.id, 
                          MerchantWithdrawals.merchant_id,
                          MerchantWithdrawals.amount,
                          MerchantWithdrawals.createdAt,
                          MerchantWithdrawals.currency,
                          MerchantWithdrawals.bank_currency,
                          MerchantWithdrawals.status,
                          MerchantWithdrawals.is_active,
                          MerchantBankAccount.bank_name,
                          Users.full_name,
                          Users.email,
                          ).join(
                               Users, Users.id == MerchantWithdrawals.merchant_id
                          ).join(
                               MerchantBankAccount, MerchantBankAccount.id == MerchantWithdrawals.bank_id
                          )
            merchant_withdrawals_object = await session.execute(stmt)
            merchant_withdrawals        = merchant_withdrawals_object.all()


            if not merchant_withdrawals:
                 return json({'error': 'No withdrawal request found'}, 404)
            

            for withdrawals in merchant_withdrawals:
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

                    # Get merchant account balance
                    merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                         and_(MerchantAccountBalance.merchant_id == withdrawals.merchant_id,
                              MerchantAccountBalance.currency    == merchant_withdrawal_currency.name
                              )
                    ))
                    merchant_account_balance_ = merchant_account_balance_obj.scalar()

                    combined_data.append({
                        'id': withdrawals.id,
                        'merchant_id': withdrawals.merchant_id,
                        'merchant_name': withdrawals.full_name,
                        'merchant_email': withdrawals.email,
                        'bank_account': withdrawals.bank_name,
                        'bankCurrency': merchant_bank_currency.name,
                        'withdrawalAmount': withdrawals.amount,
                        'withdrawalCurrency': merchant_withdrawal_currency.name,
                        'createdAt': withdrawals.createdAt,
                        'status':   withdrawals.status,
                        'is_active': withdrawals.is_active,
                        'account_balance': merchant_account_balance_.amount,
                        'account_currency': merchant_account_balance_.currency
                    })

            return json({'success': True, 'AdminMerchantExportWithdrawalRequests': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)

