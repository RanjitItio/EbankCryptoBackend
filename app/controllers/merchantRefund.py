from app.controllers.controllers import get, post
from blacksheep.server.controllers import APIController
from blacksheep import Request, json
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models3 import MerchantRefund
from Models.models2 import MerchantProdTransaction
from Models.models import Currency
from Models.PG.schema import MerchantCreateRefundSchema
from sqlmodel import select, and_, desc, func
from blacksheep import get as GET





# Raise Refund by Merchants
class MerchantRaiseRefund(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Initiate Refund'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/merchant/refund/'
    
    # Initiate new Refund by Merchant
    @auth('userauth')
    @post()
    async def create_merchantRefund(self, request: Request, schema:MerchantCreateRefundSchema):
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate user
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                # Get the request payload value
                transactionID = schema.transaction_id
                comment       = schema.comment
                amount        = schema.refund_amt
                instantRefund = schema.instant_refund

                # Get the transaction ID
                merchant_prod_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                    MerchantProdTransaction.transaction_id == transactionID
                ))
                merchant_prod_transaction  = merchant_prod_transaction_obj.scalar()

                if not merchant_prod_transaction:
                    return json({'message': 'Invalid Transaction ID'}, 400)
                
                # Transaction Currency
                transaction_currency = merchant_prod_transaction.currency

                # Get the currency id
                currency_obj = await session.execute(select(Currency).where(
                    Currency.name == transaction_currency
                ))
                currency = currency_obj.scalar()

                if not currency:
                    return json({'message': 'Invalid Transaction Currency'}, 400)
                
                # Only success transactions can be Refunded
                if merchant_prod_transaction.is_completd == False:
                    return json({'message': 'Can not raise Refund request, Transaction has not completed yet'}, 400)

                # Refund amount should be less than or equal to transaction amount
                if merchant_prod_transaction.amount < amount:
                    return json({'message': 'Refund amount should be less than or equal to Transaction amount'}, 400)
                
                # Does the merchant raised refund for same transaction id before?
                previous_refund_obj = await session.execute(select(MerchantRefund).where(
                    and_(MerchantRefund.merchant_id    == user_id,
                         MerchantRefund.transaction_id == merchant_prod_transaction.id
                         )
                ))
                previous_refund = previous_refund_obj.scalars().all()

                if previous_refund:
                    sumAmount = 0.00
                    # Sum all the refund transaction amount
                    for refundAmount in previous_refund:
                        sumAmount += refundAmount.amount

                    # If sum amount is equal to transaction amount or greater than transaction amount
                    if sumAmount > merchant_prod_transaction.amount or sumAmount == merchant_prod_transaction.amount:
                        merchant_prod_transaction.is_refunded = True

                        session.add(merchant_prod_transaction)
                        await session.commit()
                        await session.refresh(merchant_prod_transaction)

                        return json({'message': 'Can not create more refunds'}, 403)

                # Create new refund request
                refund_request = MerchantRefund(
                    merchant_id    = user_id,
                    transaction_id = merchant_prod_transaction.id,
                    amount          = amount,
                    currency        = currency.id,
                    comment         = comment,
                    instant_refund  = instantRefund,
                    instant_refund_amount = 25,
                    is_completed    = False
                )

                session.add(refund_request)
                await session.commit()
                await session.refresh(refund_request)

                return json({'success':True, 'message': 'Refund created successfully'}, 201)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        
    
    
    # Get all the Merchant Refunds
    @auth('userauth')
    @get()
    async def get_merchantRefunds(self, request: Request, limit: int = 10, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id = user_identity.claims.get('user_id')

                combined_data = []

                if limit < 0 or offset < 0:
                    return json({"message": "limit and offset value can not be negative"}, 400)
                
                # Count total rows
                count_stmt = select(func.count(MerchantRefund.id)).where(
                    MerchantRefund.merchant_id == user_id
                )
                total_rows_obj = await session.execute(count_stmt)
                total_rows = total_rows_obj.scalar()

                total_rows_count = total_rows / limit
                
                # Get all the refund made by the merchant
                stmt = select(MerchantRefund.id,
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

                              ).join(
                                  Currency, Currency.id == MerchantRefund.currency
                              ).join(
                                  MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
                              ).where(
                                  MerchantRefund.merchant_id == user_id
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
                        'instant_refund': refunds.instant_refund,
                        'instant_refund_amount': refunds.instant_refund_amount,
                        'is_completed': refunds.is_completed,
                        'transaction_id': refunds.transaction_id,
                        'amount': refunds.amount,
                        'transaction_amount': refunds.transaction_amount,
                        'createdAt': refunds.createdAt,
                        'status': refunds.status
                    })

                return json({'success': True, 'total_count': total_rows_count, 'merchant_refunds': combined_data}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



# Download all the refunds
@auth('userauth')
@GET('/api/v6/merchant/download/refunds/')
async def download_refunds(self, request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate user
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            # Get all the refund made by the merchant
            stmt = select(MerchantRefund.id,
                            Currency.name.label('currency_name'),
                            MerchantProdTransaction.transaction_id,
                            MerchantProdTransaction.currency.label('transaction_currency'),
                            MerchantProdTransaction.amount.label('transaction_amount'),
                            MerchantRefund.instant_refund,
                            MerchantRefund.instant_refund_amount,
                            MerchantRefund.amount,
                            MerchantRefund.comment,
                            MerchantRefund.createdAt,
                            MerchantRefund.status,
                            ).join(
                                Currency, Currency.id == MerchantRefund.currency
                            ).join(
                                MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
                            ).where(
                                MerchantRefund.merchant_id == user_id
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
                    'instant_refund': refunds.instant_refund,
                    'instant_refund_amount': refunds.instant_refund_amount,
                    'transaction_id': refunds.transaction_id,
                    'amount': refunds.amount,
                    'transaction_amount': refunds.transaction_amount,
                    'createdAt': refunds.createdAt,
                    'status': refunds.status
                })

            return json({'success': True, 'export_merchant_refunds': combined_data}, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)

