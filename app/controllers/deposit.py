from blacksheep.server.controllers import APIController
from Models.schemas import ExternalTransectionSchema ,WithdrawlAndDeposieSchema, DepositMoneySchema
from sqlmodel import select, and_
from database.db import async_engine, AsyncSession
from Models.models import Users ,Wallet ,Transection ,Currency , ExternalTransection
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
import uuid
from app.auth import decode_token
from blacksheep.server.responses import pretty_json
from app.controllers.controllers import get, post
from blacksheep.server.authorization import auth




#User will be able to Deposit money into wallet
class DepositController(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/deposit'

    @classmethod
    def class_name(cls):
        return "User Deposit Money"
    
    @post()
    async def create_deposit(self, transfer_money: DepositMoneySchema, request: Request):
        """
         User will be able to Deposit Money, Authenticated Route.
        """
        try:
            async with AsyncSession(async_engine) as session:

                #Authenticate user
                try:
                    header_value = request.get_first_header(b"Authorization")
                    if not header_value:
                        return json({'msg': 'Authentication Failed Please provide auth token'}, 401)
                    
                    header_value_str = header_value.decode("utf-8")

                    parts = header_value_str.split()

                    if len(parts) == 2 and parts[0] == "Bearer":
                        token = parts[1]
                        user_data = decode_token(token)

                        if user_data == 'Token has expired':
                            return json({'msg': 'Token has expired'})
                        elif user_data == 'Invalid token':
                            return json({'msg': 'Invalid token'})
                        else:
                            user_data = user_data
                            
                        userID = user_data["user_id"]
                        
                except Exception as e:
                   return json({'msg': 'Authentication Failed'}, 400)
                
                #Try to get the currency id
                try:
                    currency = await session.execute(select(Currency).where(Currency.name == transfer_money.currency))
                    currency_obj = currency.scalar()
                except Exception as e:
                    return json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
               
               #Get the selectedWallet:
                try:
                    user_wallet     = await session.execute(select(Wallet).where(Wallet.id == transfer_money.selected_wallet))
                    user_wallet_obj = user_wallet.scalars().first()

                    if not user_wallet_obj:
                        return json({'msg': 'Sender Selected FIAT wallet not fount'}, 404)
                    
                except Exception as e:
                    return json({'mag': 'Wallet error','error': f'{str(e)}'}, 400)
            
                # Get the user's wallet
                try:
                    user_wallet     = await session.execute(select(Wallet).where(and_(Wallet.user_id == userID, Wallet.currency_id == currency_obj.id)))
                    user_wallet_obj = user_wallet.scalars().first()
                except Exception as e:
                    return json({'mag': 'Wallet error','error': f'{str(e)}'}, 400)
                
                # Get the user
                try:
                    user     = await session.execute(select(Users).where(Users.id == userID))
                    user_obj = user.scalar()
                except Exception as e:
                    return json({'mag': 'Wallet error','error': f'{str(e)}'}, 400)

                if not currency_obj:
                    return json({"msg": "Invalid currency"}, status=400)
                
                if not user_wallet_obj:
                    return json({"msg": "Wallet not found"}, status=404)
                
                # Update the user's wallet balance
                # user_wallet_obj.balance += transfer_money.deposit_amount

                if user_obj.is_suspended:
                    return json({'msg': 'Your account has been suspended please contact admin for Approval'}, 400)
                
                # Create a new transaction record
                new_transaction = Transection(
                    user_id      = userID,
                    txdid        = str(uuid.uuid4()), 
                    txdtype      = 'Deposit',
                    amount       = transfer_money.deposit_amount,
                    txdfee       = transfer_money.fee,
                    totalamount  = transfer_money.total_amount,
                    txdcurrency  = currency_obj.id,
                    txdmassage   = "Deposit",
                    payment_mode = transfer_money.payment_mode,
                    txdstatus    = "Pending",
                    wallet_id    = transfer_money.selected_wallet
                )

                session.add(user_wallet_obj)
                session.add(new_transaction)
                await session.commit()
                await session.refresh(user_wallet_obj)
                await session.refresh(new_transaction)

                # Return success response with updated balance
                return json({"msg": "Deposit successful", "data": {"balance": user_wallet_obj.balance}}, status=200)
        except Exception as e:
            # Return error response with error message
            return json({"msg": "Error depositing funds", "error": str(e)}, status=400)



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
    async def get_transaction(self, request: Request, limit: int = 25, offset: int = 0):
        """
          View all the Deposit Transactions, By Admin
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                limit = limit
                offset = offset

                #Check the user is admin or Not
                try:
                    user_obj = await session.execute(select(Users).where(Users.id == user_id))
                    user_obj_data = user_obj.scalar()

                    if not user_obj_data.is_admin:
                        return json({'msg': 'Only admin can view the Transactions'}, 400)
                    
                except Exception as e:
                    return pretty_json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
                
                #Get all transaction Data
                try:
                    get_all_transaction     = await session.execute(select(Transection).where(Transection.txdtype == 'Deposit').order_by(Transection.id.desc()).limit(limit).offset(offset))
                    get_all_transaction_obj = get_all_transaction.scalars().all()
                except Exception as e:
                    return json({'msg': f'{str(e)}'}, 400)
                
                #Get the Currency
                try:
                    currency     = await session.execute(select(Currency))
                    currency_obj = currency.scalars().all()
                except Exception as e:
                    return pretty_json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
                
                #Get the converted currency wallet
                try:
                    converted_currency_wallet     = await session.execute(select(Wallet))
                    converted_currency_wallet_obj = converted_currency_wallet.scalars().all()
                except Exception as e:
                    return pretty_json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
                
                #Get the user data
                try:
                    user_obj      = await session.execute(select(Users))
                    user_obj_data = user_obj.scalars().all()
                except Exception as e:
                    return json({'msg': 'User not found'}, 400)

                currency_dict = {currency.id: currency for currency in currency_obj}
                user_dict     = {user.id: user for user in user_obj_data}
                converted_currency_wallet_dict = {wallet.id: wallet for wallet in converted_currency_wallet_obj}
                combined_data = []
                
                for transaction in get_all_transaction_obj:
                        currency_id             = transaction.txdcurrency
                        currency_data           = currency_dict.get(currency_id)
                        
                        user_id   = transaction.user_id
                        user_data = user_dict.get(user_id)

                        converted_currency_id = transaction.wallet_id
                        converted_currency    = converted_currency_wallet_dict.get(converted_currency_id)

                        combined_data.append({
                            'transaction': transaction,
                            'currency': currency_data,
                            'user': user_data,
                            'converted_currency': converted_currency if converted_currency else None
                        })
                
                if not get_all_transaction_obj:
                    return json({'msg': "No Transaction available to show"}, 404)
                
                return json({'msg': 'Deposit Transaction data fetched successfully', 'data': combined_data})
            
        except Exception as e:
            return json({'error': f'{str(e)}'}, 400)
        
    