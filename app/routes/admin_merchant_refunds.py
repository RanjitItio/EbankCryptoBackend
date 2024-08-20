from blacksheep import get, put, Request, json
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users, Currency
from Models.models2 import MerchantProdTransaction, MerchantAccountBalance
from Models.models3 import MerchantRefund
from Models.Admin.PG.schema import AdminUpdateMerchantRefundSchema
from sqlmodel import select, and_, desc, func, cast, Date, Time, or_
from datetime import datetime




# Get all the merchant Refund Transactions
@auth('userauth')
@get('/api/v6/admin/merchant/refunds/')
async def Admin_Merchant_Refunds(request: Request, limit: int = 10, offset: int = 0):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate user as admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            adminUserObj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            adminUser = adminUserObj.scalar()

            if not adminUser.is_admin:
                return json({'error': 'Admin authentication Failed'}, 401)
            # Admin authentication ends here

            if limit < 0 or offset < 0:
                return json({"message": "limit and offset value can not be negative"}, 400)
            
            # Count total rows
            count_stmt = select(func.count(MerchantRefund.id))
            total_rows_obj = await session.execute(count_stmt)
            total_rows = total_rows_obj.scalar()

            total_rows_count = total_rows / limit

            # Get all the refund made by the merchant
            stmt = select(
                MerchantRefund.id,
                MerchantRefund.merchant_id,
                MerchantRefund.instant_refund,
                MerchantRefund.instant_refund_amount,
                MerchantRefund.is_completed,
                MerchantRefund.amount,
                MerchantRefund.comment,
                MerchantRefund.createdAt,
                MerchantRefund.status,

                Currency.name.label('currency_name'),
                MerchantProdTransaction.transaction_id,
                MerchantProdTransaction.currency.label('transaction_currency'),
                MerchantProdTransaction.amount.label('transaction_amount'),
                Users.full_name.label('merchant_name'),
                Users.email.label('merchant_email'),

                ).join(
                    Currency, Currency.id == MerchantRefund.currency
                ).join(
                    MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
                ).join(
                     Users, Users.id == MerchantRefund.merchant_id
                ).order_by(
                    desc(MerchantRefund.id)

                ).limit(limit).offset(offset)
            
            merchant_refunds_obj = await session.execute(stmt)
            merchant_refunds = merchant_refunds_obj.fetchall()

            if not merchant_refunds:
                return json({'message': 'No refund requests available'}, 404)
            
            for refunds in merchant_refunds:
                    combined_data.append({
                        'id': refunds.id,
                        "currency": refunds.currency_name,
                        "transaction_currency": refunds.transaction_currency,
                        "merchant_id": refunds.merchant_id,
                        'merchant_name': refunds.merchant_name,
                        'merchant_email': refunds.merchant_email,
                        'instant_refund': refunds.instant_refund,
                        'instant_refund_amount': refunds.instant_refund_amount,
                        'is_completed': refunds.is_completed,
                        'transaction_id': refunds.transaction_id,
                        'amount': refunds.amount,
                        'transaction_amount': refunds.transaction_amount,
                        'createdAt': refunds.createdAt,
                        'status': refunds.status
                    })

            return json({'success': True, 'total_count': total_rows_count, 'admin_merchant_refunds': combined_data}, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



# Update Merchant Refund by Admin
@auth('userauth')
@put('/api/v6/admin/merchant/update/refunds/')
async def MerchantRefundUpdate(request: Request, schema: AdminUpdateMerchantRefundSchema):
    try:
        async with AsyncSession(async_engine) as session:
               # Authenticate user as Admin
               user_identity = request.identity
               user_id = user_identity.claims.get('user_id')

               adminUserObj = await session.execute(select(Users).where(Users.id == user_id))
               adminUser = adminUserObj.scalar()

               if not adminUser.is_admin:
                    return json({'message': 'Admin authentication failed'}, 401)
               # Admin authentication Ends

               # Get the payload data
               merchantID    = schema.merchant_id
               refundID      = schema.refund_id
               transactionID = schema.transaction_id
               status        =  schema.status

               # Get the Merchant refund transaction
               merchantRefundTransactionObj = await session.execute(select(MerchantRefund).where(
                    and_(MerchantRefund.merchant_id == merchantID,
                        MerchantRefund.id == refundID
                         )
               ))
               merchantRefundTransaction = merchantRefundTransactionObj.scalar()

               ## If the transaction already approved
               if merchantRefundTransaction.status == 'Approved':
                    return json({'message': 'Can not perform the same action again'}, 405)
               
               # Update database
               merchantRefundTransaction.status = status

               if status == 'Approved':
                    merchantRefundTransaction.is_completed = True

                    # Get the transaction related to the Refund
                    merchant_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                            and_(MerchantProdTransaction.transaction_id == transactionID,
                                 MerchantProdTransaction.merchant_id == merchantID
                                 )
                    ))
                    merchant_transaction = merchant_transaction_obj.scalar()

                    # Update the transaction as refunded
                    merchant_transaction.is_refunded = True

                    # Get the Merchant account balance
                    merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                         and_(MerchantAccountBalance.merchant_id == merchantID,
                              MerchantAccountBalance.currency    == merchant_transaction.currency)
                    ))
                    merchant_account_balance = merchant_account_balance_obj.scalar()

                    # Deduct the merchant Account balance
                    merchant_account_balance.amount -= merchantRefundTransaction.amount

                    
                    session.add(merchant_transaction)
                    session.add(merchant_account_balance)
                    await session.commit()
                    await session.refresh(merchant_transaction)
                    await session.refresh(merchant_account_balance)

               session.add(merchantRefundTransaction)
               await session.commit()
               await session.refresh(merchantRefundTransaction)

               return json({'success': True, 'message': 'Updated Successfully'}, 200)
               
    except Exception as e:
         return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    



# Export all Merchant Refund Transactions
@auth('userauth')
@get('/api/v6/admin/merchant/pg/export/refunds/')
async def ExportMerchantRefunds(request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate user as admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            adminUserObj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            adminUser = adminUserObj.scalar()

            if not adminUser.is_admin:
                return json({'error': 'Admin authentication Failed'}, 401)
            # Admin authentication ends here

            # Get all the refunds made by the merchant
            stmt = select(
                MerchantRefund.id,
                MerchantRefund.merchant_id,
                MerchantRefund.instant_refund,
                MerchantRefund.instant_refund_amount,
                MerchantRefund.is_completed,
                MerchantRefund.amount,
                MerchantRefund.comment,
                MerchantRefund.createdAt,
                MerchantRefund.status,

                Currency.name.label('currency_name'),
                MerchantProdTransaction.transaction_id,
                MerchantProdTransaction.currency.label('transaction_currency'),
                MerchantProdTransaction.amount.label('transaction_amount'),
                Users.full_name.label('merchant_name'),
                Users.email.label('merchant_email'),

                ).join(
                    Currency, Currency.id == MerchantRefund.currency
                ).join(
                    MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
                ).join(
                     Users, Users.id == MerchantRefund.merchant_id
                ).order_by(
                    desc(MerchantRefund.id)

                )
            
            merchant_refunds_obj = await session.execute(stmt)
            merchant_refunds = merchant_refunds_obj.fetchall()

            if not merchant_refunds:
                return json({'message': 'No refund requests available'}, 404)
            
            for refunds in merchant_refunds:
                combined_data.append({
                    'id': refunds.id,
                    "currency": refunds.currency_name,
                    "transaction_currency": refunds.transaction_currency,
                    "merchant_id": refunds.merchant_id,
                    'merchant_name': refunds.merchant_name,
                    'merchant_email': refunds.merchant_email,
                    'instant_refund': refunds.instant_refund,
                    'instant_refund_amount': refunds.instant_refund_amount,
                    'is_completed': refunds.is_completed,
                    'transaction_id': refunds.transaction_id,
                    'amount': refunds.amount,
                    'transaction_amount': refunds.transaction_amount,
                    'createdAt': refunds.createdAt,
                    'status': refunds.status
                })

            return json({'success': True, 'admin_merchant_refunds_export': combined_data}, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    


# Search Merchant Refund Transactions
@auth('userauth')
@get('/api/v6/admin/merchant/refund/search/')
async def SearchMerchantRefunds(request: Request,query: str):
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
            # Admin authentication ends

            query_date = None
            query_time = None
            instant_refund_query = None

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

            if query == 'Yes':
                instant_refund_query = True
            elif query == 'No':
                instant_refund_query = False


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

            # Search Refund amount wise
            refund_amount_obj = await session.execute(
                select(MerchantRefund).where(
                        MerchantRefund.amount == query_as_float
                ) if query_as_float is not None else select(MerchantRefund).where(
                        MerchantRefund.amount == 0.00
                )
            )
            refund_amount = refund_amount_obj.scalars().all()

            # Search Instant Refund wise
            instant_refund_obj = await session.execute(
                select(MerchantRefund).where(
                        MerchantRefund.instant_refund == instant_refund_query
                ) 
            )
            instant_refund = instant_refund_obj.scalars().all()

             # Search status wise
            refund_status_obj = await session.execute(
                select(MerchantRefund).where(MerchantRefund.status == query)
                )
            refund_status = refund_status_obj.scalars().all()

            stmt = select(
                MerchantRefund.id,
                MerchantRefund.merchant_id,
                MerchantRefund.instant_refund,
                MerchantRefund.instant_refund_amount,
                MerchantRefund.is_completed,
                MerchantRefund.amount,
                MerchantRefund.comment,
                MerchantRefund.createdAt,
                MerchantRefund.status,

                Currency.name.label('currency_name'),
                MerchantProdTransaction.transaction_id,
                MerchantProdTransaction.currency.label('transaction_currency'),
                MerchantProdTransaction.amount.label('transaction_amount'),
                Users.full_name.label('merchant_name'),
                Users.email.label('merchant_email'),

                ).join(
                    Currency, Currency.id == MerchantRefund.currency
                ).join(
                    MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
                ).join(
                     Users, Users.id == MerchantRefund.merchant_id
                ).order_by(
                    desc(MerchantRefund.id)
                )
            
            conditions = []

            if user_full_name:
                conditions.append(MerchantRefund.merchant_id.in_([user.id for user in user_full_name]))

            elif user_email:
                conditions.append(MerchantRefund.merchant_id == user_email.id)

            elif currency:
                conditions.append(MerchantRefund.currency == currency.id)

            elif refund_amount:
                conditions.append(MerchantRefund.amount.in_([wa.amount for wa in refund_amount]))

            elif instant_refund:
                conditions.append(MerchantRefund.instant_refund.in_([wa.instant_refund for wa in instant_refund]))

            elif refund_status:
                conditions.append(MerchantRefund.status.in_([ws.status for ws in refund_status]))

            if query_date:
                conditions.append(cast(MerchantRefund.createdAt, Date) == query_date)

            if query_time:
                conditions.append(cast(MerchantRefund.createdAt, Time) == query_time)

            if conditions:
                stmt = stmt.where(or_(*conditions))

            merchant_refunds_object = await session.execute(stmt)
            merchant_refunds        = merchant_refunds_object.fetchall()

            merchant_refunds_data = []

            for refunds in merchant_refunds:
                merchant_refunds_data.append({
                    'id': refunds.id,
                    "currency": refunds.currency_name,
                    "transaction_currency": refunds.transaction_currency,
                    "merchant_id": refunds.merchant_id,
                    'merchant_name': refunds.merchant_name,
                    'merchant_email': refunds.merchant_email,
                    'instant_refund': refunds.instant_refund,
                    'instant_refund_amount': refunds.instant_refund_amount,
                    'is_completed': refunds.is_completed,
                    'transaction_id': refunds.transaction_id,
                    'amount': refunds.amount,
                    'transaction_amount': refunds.transaction_amount,
                    'createdAt': refunds.createdAt,
                    'status': refunds.status
                })

            return json({'success': True, 'searched_merchant_refund': merchant_refunds_data}, 200)

    except Exception as e:
         return json({'error':'Server Error', 'message': f'{str(e)}'}, 500) 