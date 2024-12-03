from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from app.controllers.controllers import post
from Models.schemas import DepositMoneySchema
from database.db import AsyncSession, async_engine
from Models.models import Currency, Wallet, Users
from Models.models4 import DepositTransaction
from app.CryptoFiatController.uniqueID import UniqueDepositTransactionID
from sqlmodel import select, and_






#User will be able to Deposit money into wallet
class DepositController(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/deposit/'

    @classmethod
    def class_name(cls):
        return "User Deposit Money"
    
    @auth('userauth')
    @post()
    async def create_deposit(self, deposit_schema: DepositMoneySchema, request: Request):
        """
            This API Endpoint will create Deposit Transaction object with specified deposit_schema.<br/><br/>

            Parameters:<br/><br/>
                - request(Request): The HTTP request object containing the user's identity and payload data.<br/>
                - deposit_schema(DepositMoneySchema): The schema object containing the currency, deposit amount, selected wallet, fee, total amount, and payment mode.<br/><br/>

            Returns:<br/>
             - JSON response with success status, message, and transaction id if successful.<br/>
             - JSON response with error status and message if an exception occurs.<br/><br/>

            Raise:<br/>
              - BadRequest if the payload data is invalid.<br/>
              - Unauthorized if the user is not authenticated.<br/><br/>

            Error Message:<br/>
             - Error Response status code 400 - "message": "Suspended User".<br/>
             - Error Response status code 404 - "message": "Sender Selected FIAT wallet not fount".<br/>
             - Error Response status code 400 - "message": "Invalid currency".<br/>
             - Error Response status code 400 - "message": "Wallet not found".<br/>
             - Error Response status code 400 - "message": "Your account has been suspended please contact admin for Approval".<br/>
             - Error Response status code 500 - "error": "Server Error".<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                #Authenticate user
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')
                
                # Get the payload data
                deposit__currency = deposit_schema.currency
                deposit__amount   = deposit_schema.deposit_amount
                selected__wallet  = deposit_schema.selected_wallet
                deposit__fee      = deposit_schema.fee
                total__amount     = deposit_schema.total_amount
                payment__mode     = deposit_schema.payment_mode

                ## Get The user 
                fiat_user_obj = await session.execute(select(Users).where(
                    Users.id == user_id
                ))
                fiat_user = fiat_user_obj.scalar()

                ## If user has been suspended
                if fiat_user.is_suspended:
                    return json({'message': 'Suspended User'}, 400)
                

                # Get Currency
                currency     = await session.execute(select(Currency).where(
                    Currency.name == deposit__currency
                    ))
                currency_obj = currency.scalar()
               
               # Get the wallet related to Currency of user
                user_selected_wallet_obj = await session.execute(select(Wallet).where(
                    Wallet.id == selected__wallet
                    ))
                user_selected_wallet     = user_selected_wallet_obj.scalar()
            

                if not user_selected_wallet:
                    return json({'msg': 'Sender Selected FIAT wallet not fount'}, 404)
            
                # Get the user's wallet
                try:
                    user_wallet = await session.execute(select(Wallet).where(
                        and_(
                            Wallet.user_id == user_id, 
                            Wallet.currency_id == currency_obj.id
                        )))
                    user_wallet_obj = user_wallet.scalars().first()

                except Exception as e:
                    return json({'error': f'{str(e)}'}, 400)
                
                # Get the user
                user_obj     = await session.execute(select(Users).where(Users.id == user_id))
                user         = user_obj.scalar()

                if not currency_obj:
                    return json({"msg": "Invalid currency"}, 400)
                
                if not user_wallet_obj:
                    return json({"msg": "Wallet not found"}, 404)
                
                if user.is_suspended:
                    return json({'msg': 'Your account has been suspended please contact admin for Approval'}, 400)
                
                # Get the unique transaction Id
                unique_id = await UniqueDepositTransactionID()

                # Create a new transaction record
                new_transaction = DepositTransaction(
                    user_id         = user_id,
                    transaction_id  = unique_id,
                    amount          = deposit__amount,
                    currency        = currency_obj.id,
                    transaction_fee = deposit__fee,
                    payout_amount   = total__amount,
                    status          = "Pending",
                    payment_mode    = payment__mode,
                    is_completed    = False,
                    selected_wallet = user_selected_wallet.id
                )

                session.add(new_transaction)
                await session.commit()
                await session.refresh(new_transaction)

                return json({
                    "msg": "Deposit successful", 
                    }, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)