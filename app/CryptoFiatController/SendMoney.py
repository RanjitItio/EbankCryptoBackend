from Models.models import Users ,Wallet ,Currency , ReceiverDetails
from Models.models4 import TransferTransaction
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from app.controllers.controllers import get, post
from Models.schemas import TransferMoneySchema
from database.db import async_engine, AsyncSession
from blacksheep import Request, json
from sqlmodel import select, and_
import time
import uuid




## Send money for Fiat user
class TransferMoneyController(APIController):
    
    @classmethod
    def route(cls):
        return '/api/v1/user/send/money/'

    @classmethod
    def class_name(cls):
        return "Send Money"
    

    @auth('userauth')
    @post()
    async def send_money(self, transfer_data: TransferMoneySchema, request: Request):
        """
            This API Endpoint transfers money from user's wallet to another user's wallet and bank account.<br/><br/>

            Parameters:<br/>
                - request (Request): The incoming request object containing user identity and payload data.<br/>
                - transfer_data (TransferMoneySchema): The schema object containing the transfer details.<br/><br/>
            
            Returns:<br/>
            - JSON response with success status 200 and msg if successful.<br/>
            - JSON response with error status 400 and message if invalid request data.<br/>
            - JSON response with error status 500 and message if an error occurs during database operations.<br/><br/>

            Error message:<br/>
              - Your account has been suspended please contact admin for Approval - if the user is suspended.<br/>
              - Sender currency does not exist - if the sender currency does not exist.<br/>
              - Receiver currency does not exist - if the receiver currency does not exist.<br/>
              - Sender do not have wallet - if the sender does not have wallet.<br/>
              - Sender donot have sufficient balance in wallet - if the sender does not have sufficient balance in wallet.<br/>
              - Recipient email does not exist" - if the recipient does not.<br/>
              - Recipient wallet not found - if the recipient does not have wallet.<br/><br/>

            Raise:<br/>
                - BadRequest - if the request is invalid.<br/>
                - InternalServerError - if an error occurs during database operations.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:

                user_identity    = request.identity
                user_id          = user_identity.claims.get("user_id") if user_identity else None

                unique_transaction_id = str(uuid.uuid4())
                timestamp = str(int(time.time()))

                # Get the user
                user = await session.execute(select(Users).where(
                    Users.id == user_id
                    ))
                user_obj = user.scalar()
                
                #If the user has been Suspended then Transaction can not be performed by this user.
                if user_obj.is_suspended:
                    return json({'message': 'Your account has been suspended please contact admin for Approval'}, 403)
                
                # Get the Sender Currency
                sender_currency = await session.execute(select(Currency).where(
                    Currency.name == transfer_data.send_currency
                    ))
                sender_currency_obj = sender_currency.scalar()

                if not sender_currency_obj:
                    return json({'message': 'Sender currency does not exist'}, 404)
                
                # Get Receiver Currency
                receiver_currency     = await session.execute(select(Currency).where(Currency.name == transfer_data.rec_currency))
                receiver_currency_obj = receiver_currency.scalar()

                if not receiver_currency_obj:
                    return json({'message': 'Receiver currency does not exist'}, 404)
                

                # Get sender wallet
                sender_wallet     = await session.execute(select(Wallet).where(and_(Wallet.user_id == user_id, Wallet.currency_id == sender_currency_obj.id)))
                sender_wallet_obj = sender_wallet.scalar()

                if not sender_wallet_obj:
                    return json({"message": "Sender do not have wallet"}, 404)
                
                if sender_wallet_obj.balance < transfer_data.total_amount:
                        return json({'message': 'Sender donot have sufficient balance in wallet'}, 403)
                
                #===========================================
                # If the recipient payment method is wallet
                #===========================================
                if transfer_data.rec_pay_mode == 'Wallet':
                    
                    #Check recipient exist as a user or not
                    recipient     = await session.execute(select(Users).where(
                        Users.email == transfer_data.rec_email
                        ))
                    recipient_obj = recipient.scalars().first()

                    if not recipient_obj:
                        return json({"message": "Recipient email does not exist"}, status=404)
                    
                    # Receiver wallet
                    recipient_wallet     = await session.execute(select(Wallet).where(
                        and_(
                            Wallet.user_id     == recipient_obj.id, 
                            Wallet.currency_id == receiver_currency_obj.id
                            )
                        ))
                    recipient_wallet_obj = recipient_wallet.scalar()

                    if not recipient_wallet_obj:
                        return json({'message': 'Recipient wallet not found'}, 404)
                    
                    ## If sender and receiver are the same
                    if recipient_obj.id == user_obj.id:
                        return json({'message': 'Cannot transfer to same wallet'}, 404)
                    

                    addtransection = TransferTransaction(
                        user_id         = user_id,
                        transaction_id  = f"{timestamp}-{unique_transaction_id}",
                        receiver        = recipient_obj.id,
                        amount          = transfer_data.send_amount,
                        transaction_fee = transfer_data.fee,
                        payout_amount   = transfer_data.total_amount,
                        currency        = sender_currency_obj.id,
                        massage         = transfer_data.purpose,
                        status          = 'Pending',
                        payment_mode    = transfer_data.sender_payment_mode,

                        receiver_payment_mode = transfer_data.rec_pay_mode,
                        receiver_currency     = receiver_currency_obj.id
                    )

                    session.add(addtransection)
                    await session.commit()
                    await session.refresh(addtransection)

                    return json({'msg': 'Transfer Successfull please wait for Admin Approval'}, 200)
                
                #===========================================
                # If the recipient payment method is other than Bank
                #===========================================
                else:

                    receiver_details = ReceiverDetails(
                        full_name     = transfer_data.rec_full_name,
                        email         = transfer_data.rec_email,
                        mobile_number = transfer_data.rec_phoneno,
                        pay_via       = transfer_data.rec_pay_mode,
                        bank_name     = transfer_data.rec_bank_name,
                        acc_number    = transfer_data.rec_acc_no,
                        ifsc_code     = transfer_data.rec_ifsc,
                        add_info      = transfer_data.rec_add_info,
                        address       = transfer_data.rec_address,
                        currency      = receiver_currency_obj.id
                    )
                    session.add(receiver_details)

                    addtransection   = TransferTransaction(
                        user_id         = user_id,
                        transaction_id  = f"{timestamp}-{unique_transaction_id}",
                        amount          = transfer_data.send_amount,
                        transaction_fee = transfer_data.fee,
                        payout_amount   = transfer_data.total_amount,
                        currency        = sender_currency_obj.id,
                        massage         = transfer_data.purpose,
                        status          = 'Pending',
                        payment_mode = transfer_data.sender_payment_mode,

                        receiver_payment_mode = transfer_data.rec_pay_mode,
                        receiver_currency     = receiver_currency_obj.id
                    )

                    await session.commit()
                    await session.refresh(receiver_details)

                    addtransection.receiver_detail  = receiver_details.id
                    
                    session.add(addtransection)
                    await session.commit()
                    await session.refresh(addtransection)

                    return json({'msg': 'Transaction Successfull please wait for Admin Approval'}, 200)
                
        except Exception as e:
                return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)

