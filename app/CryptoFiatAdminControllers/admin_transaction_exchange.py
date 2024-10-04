from app.controllers.controllers import get, post, put
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from sqlmodel import select, desc, and_, func
from Models.models import Users, Currency, Wallet
from Models.models4 import FIATExchangeMoney
from Models.FIAT.Schema import AdminUpdateExchangeMoneySchema



# Exchange Money Controller for Admin section
class AdminFiatExchangeMoneyController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Admin Exchange Money Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/admin/exchange/money/'
    

    ## Get all Exchange Money Transactions
    @auth('userauth')
    @get()
    async def get_fiat_exchange_requests(self, request: Request, limit: int = 10, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity   = request.identity
                AdminID          = user_identity.claims.get("user_id") if user_identity else None

                # Admin Authentication
                admin_obj      = await session.execute(select(Users).where(Users.id == AdminID))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                # Admin authentication ends

                combined_data = []

                # Count total available rows
                row_stmt = select(func.count(FIATExchangeMoney.id))
                exe_row_stmt = await session.execute(row_stmt)
                exchange_row_count = exe_row_stmt.scalar()

                total_exchange_rows = exchange_row_count / limit
                
                stmt = select(
                    FIATExchangeMoney.id,
                    FIATExchangeMoney.from_currency,
                    FIATExchangeMoney.to_currency,
                    FIATExchangeMoney.exchange_amount,
                    FIATExchangeMoney.converted_amount,
                    FIATExchangeMoney.transaction_fee,
                    FIATExchangeMoney.created_At,
                    FIATExchangeMoney.is_completed,
                    FIATExchangeMoney.user_id,
                    FIATExchangeMoney.status,

                    Users.full_name.label('user_name'),
                    Users.email.label('user_email')
                ).join(
                    Users, Users.id == FIATExchangeMoney.user_id
                ).order_by(
                    desc(FIATExchangeMoney.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                fiat_exchange_money_obj = await session.execute(stmt)
                fiat_exchange_money     = fiat_exchange_money_obj.fetchall()

                if not fiat_exchange_money:
                    return json({'message': 'No data found'}, 404)

                for transaction in fiat_exchange_money:
                    # From Currency
                    from_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == transaction.from_currency
                    ))
                    from_currency = from_currency_obj.scalar()

                    # To Currency
                    to_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == transaction.to_currency
                    ))
                    to_currency = to_currency_obj.scalar()

                    combined_data.append({
                        "id": transaction.id,
                        "to_currency": to_currency.name,
                        "converted_amount": transaction.converted_amount,
                        "is_completed": transaction.is_completed,
                        "from_currency": from_currency.name,
                        "exchange_amount": transaction.exchange_amount,
                        "user_id": transaction.user_id,
                        "transaction_fee": transaction.transaction_fee,
                        "created_At": transaction.created_At,
                        "user_name": transaction.user_name,
                        'user_email': transaction.user_email,
                        "status": transaction.status
                    })

                return json({
                    'success': True,
                    'all_exchange_money_data': combined_data,
                    'total_row_count': total_exchange_rows
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        

    ## update Exchange Money Transaction
    @auth('userauth')
    @put()
    async def update_exchange_money(self, request: Request, schema: AdminUpdateExchangeMoneySchema):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity   = request.identity
                AdminID          = user_identity.claims.get("user_id") if user_identity else None

                # Admin Authentication
                admin_obj      = await session.execute(select(Users).where(Users.id == AdminID))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                # Admin authentication ends

                # Get payload data
                status            = schema.status
                exchange_money_id = int(schema.exchange_money_id)
                convertedAmount   = float(schema.converted_amount)

                # Get the Exchange Money request
                exchange_money_req_obj = await session.execute(select(FIATExchangeMoney).where(
                    FIATExchangeMoney.id == exchange_money_id
                ))
                exchange_money_req = exchange_money_req_obj.scalar()

                if not exchange_money_req:
                    return json({'message': 'Transaction not found'}, 404)

                if exchange_money_req.is_completed:
                    return json({'message': 'Transaction has been completed'}, 400)

                # get the user wallet
                user_from_wallet_obj =  await session.execute(select(Wallet).where(
                    and_(
                        Wallet.currency_id == exchange_money_req.from_currency,
                        Wallet.user_id     == exchange_money_req.user_id
                    )
                ))
                user_from_wallet = user_from_wallet_obj.scalar()

                if not user_from_wallet:
                    return json({'message': 'From Wallet not found'}, 404)
                

                # get the user wallet
                user_to_wallet_obj =  await session.execute(select(Wallet).where(
                    and_(
                        Wallet.currency_id == exchange_money_req.to_currency,
                        Wallet.user_id     == exchange_money_req.user_id
                    )
                ))
                user_to_wallet = user_to_wallet_obj.scalar()

                if not user_to_wallet:
                    return json({'message': 'Received Wallet not found'}, 404)
                
                if status == 'Approved':
                    if user_from_wallet.balance < exchange_money_req.exchange_amount:
                        return json({'message': 'Do not have sufficient balance in account'}, 400)
                    
                    # Add and deduct from wallet to respective Wallet
                    total_deduct_amount = exchange_money_req.exchange_amount + exchange_money_req.transaction_fee

                    user_from_wallet.balance -= total_deduct_amount
                    user_to_wallet.balance += convertedAmount

                    # Update transaction status
                    exchange_money_req.status       = 'Approved'
                    exchange_money_req.is_completed = True

                    session.add(exchange_money_req)
                    session.add(user_from_wallet)
                    session.add(user_to_wallet)
                    await session.commit()
                    await session.refresh(exchange_money_req)
                    await session.refresh(user_to_wallet)
                    await session.refresh(user_from_wallet)

                    return json({
                        'success': True,
                        'message': 'Updated successfully'
                        }, 200)
                else:
                    exchange_money_req.status = status
                    exchange_money_req.is_completed = False

                    session.add(exchange_money_req)
                    await session.commit()
                    await session.refresh(exchange_money_req)

                    return json({
                        'success': True,
                        'message': 'Updated successfully'
                        }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)


    