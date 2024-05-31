from blacksheep.server.controllers import APIController
from Models.schemas import TransferMoneySchema , ExternalTransectionSchema
from sqlmodel import select, and_
from database.db import async_engine, AsyncSession
from Models.models import Users ,Wallet ,Transection ,Currency , ExternalTransection, SenderDetails, ReceiverDetails
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import  decode_token
import time
import uuid
from app.controllers.controllers import get, post
from blacksheep.server.authorization import auth




#User will be able to Transfer money to Another user
class TransferMoneyController(APIController):
    
    @classmethod
    def route(cls):
        return '/api/v1/user/transfer_money'

    @classmethod
    def class_name(cls):
        return "Transfer Money"
    

    @auth('userauth')
    @post()
    async def create_transfermoney(self, transfer_data: TransferMoneySchema, request: Request):
        """
          User will be able to Transfer amount to another user, Authenticated route.
        """
        try:
            async with AsyncSession(async_engine) as session:

                user_identity    = request.identity
                user_id          = user_identity.claims.get("user_id") if user_identity else None

                unique_transaction_id = uuid.uuid4()
                timestamp = str(int(time.time()))

                # Get the user
                try:
                    user     = await session.execute(select(Users).where(Users.id == user_id))
                    user_obj = user.scalar()
                except Exception as e:
                    return json({'mag': 'Wallet error','error': f'{str(e)}'}, 400)
                
                #If the user has been Suspended then Transaction can not be performed by this user.
                if user_obj.is_suspended:
                    return json({'msg': 'Your account has been suspended please contact admin for Approval'}, 403)
                
                #Try to get the currency id
                try:
                    sender_currency     = await session.execute(select(Currency).where(Currency.name == transfer_data.send_currency))
                    sender_currency_obj = sender_currency.scalar()

                    if not sender_currency_obj:
                        return json({'msg': 'Sender currency does not exist'}, 404)
                    
                except Exception as e:
                    return json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
                
                try:
                    receiver_currency     = await session.execute(select(Currency).where(Currency.name == transfer_data.rec_currency))
                    receiver_currency_obj = receiver_currency.scalar()

                    if not receiver_currency_obj:
                        return json({'msg': 'Sender currency does not exist'}, 404)
                    
                except Exception as e:
                    return json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
                
                #Sender Wallet Exists or not
                try:
                    sender_wallet     = await session.execute(select(Wallet).where(and_(Wallet.user_id == user_id, Wallet.currency_id == sender_currency_obj.id)))
                    sender_wallet_obj = sender_wallet.scalar()

                    if not sender_wallet_obj:
                        return json({"msg": "Sender do not have wallet"}, status=404)

                except Exception as e:
                    return json({'msg': 'Unable to identify Sendeer wallet', 'error': f'{str(e)}'}, 400)
                
                
                #===========================================
                #If the recipient payment method is wallet
                #===========================================
                if transfer_data.rec_pay_mode == 'Wallet':
                    
                    #Check recipient exist as a user or not
                    try:
                        recipient     = await session.execute(select(Users).where(Users.email == transfer_data.rec_email))
                        recipient_obj = recipient.scalars().first()

                        if not recipient_obj:
                            return json({"msg": "Recipient email does not exist"}, status=404)
                        
                    except Exception as e:
                        return json({'msg': 'Unable to identify Recipient'}, 400)
                    
                    #Check Recipient wallet exists or not
                    try:
                        recipient_wallet     = await session.execute(select(Wallet).where(Wallet.user_id == recipient_obj.id and Wallet.currency_id == receiver_currency_obj.id))
                        recipient_wallet_obj = recipient_wallet.scalars().first()

                        if not recipient_wallet_obj:
                            return json({'msg': 'Recipient wallet not found'}, 404)
                    
                    except Exception as e:
                        return json({'msg': 'Unable to locate recipient Wallet'}, 400)
                    
                    if sender_wallet_obj.id == recipient_wallet_obj.id:
                        return json({'msg': 'Cannot transfer to same wallet'}, 404)
                    
                    addtransection   = Transection(
                                user_id      = user_id,
                                txdid        = f"{timestamp}-{unique_transaction_id}",
                                txdrecever   = recipient_obj.id,
                                amount       = transfer_data.send_amount,
                                txdfee       = transfer_data.fee,
                                totalamount  = transfer_data.total_amount,
                                txdcurrency  = sender_currency_obj.id,
                                txdmassage   = transfer_data.purpose,
                                txdstatus    = 'Pending',
                                txdtype      = 'Transfer',
                                payment_mode = transfer_data.sender_payment_mode,
                                rec_pay_mode = transfer_data.rec_pay_mode,
                                rec_currency = receiver_currency_obj.id
                            )

                    session.add(addtransection)
                    await session.commit()
                    await session.refresh(addtransection)

                    return json({'msg': 'Transafer Successfull please wait for Admin Approval'}, 200)
                
                #===========================================
                #If the recipient payment method is Bank
                #===========================================
                elif transfer_data.rec_pay_mode == 'Bank':

                    
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
                    

                    addtransection   = Transection(
                        user_id      = user_id,
                        txdid        = f"{timestamp}-{unique_transaction_id}",
                        amount       = transfer_data.send_amount,
                        txdfee       = transfer_data.fee,
                        totalamount  = transfer_data.total_amount,
                        txdcurrency  = sender_currency_obj.id,
                        txdmassage   = transfer_data.purpose,
                        txdstatus    = 'Pending',
                        txdtype      = 'Transfer',
                        payment_mode = transfer_data.sender_payment_mode,
                        rec_pay_mode = transfer_data.rec_pay_mode,
                        rec_currency = receiver_currency_obj.id
                    )

                    await session.commit()
                    await session.refresh(receiver_details)

                    addtransection.rec_detail  = receiver_details.id
                    
                    session.add(addtransection)
                    await session.commit()
                    await session.refresh(addtransection)

                    return json({'msg': 'Transaction Successfull please wait for Admin Approval'}, 200)

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

                    addtransection   = Transection(
                        user_id      = user_id,
                        txdid        = f"{timestamp}-{unique_transaction_id}",
                        amount       = transfer_data.send_amount,
                        txdfee       = transfer_data.fee,
                        totalamount  = transfer_data.total_amount,
                        txdcurrency  = sender_currency_obj.id,
                        txdmassage   = transfer_data.purpose,
                        txdstatus    = 'Pending',
                        txdtype      = 'Transfer',
                        payment_mode = transfer_data.sender_payment_mode,
                        rec_pay_mode = transfer_data.rec_pay_mode,
                        rec_currency = receiver_currency_obj.id
                    )

                    await session.commit()
                    await session.refresh(receiver_details)

                    addtransection.rec_detail  = receiver_details.id

                    session.add(addtransection)
                    await session.commit()
                    await session.refresh(addtransection)

                    return json({'msg': 'Transaction Successfull please wait for Admin Approval'}, 200)

        except Exception as e:
                return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)




class ExternalMoneyTransferController(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/external_transfer_money'

    @classmethod
    def class_name(cls):
        return "Transfer Money"
    
    @post()
    async def transfer_money(self, transfer_data: ExternalTransectionSchema, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # Get the user making the transfer
                # user = await session.execute(select(Users).where(Users.id == transfer_data.user_id))
                # user_obj = user.scalars().first()
                # Get the recipient user
                # recipient = await session.execute(select(Users).where(Users.email == transfer_data.reciver))
                # recipient_obj = recipient.scalars().first()
                user_wallet = await session.execute(select(Wallet).where(Wallet.user_id ==transfer_data.user_id and Wallet.currency_id == transfer_data.txdcurrency))
                user_wallet_obj = user_wallet.scalars().first()
                # Check if the user has enough balance
                if user_wallet_obj.balance >= transfer_data.amount:
                    # Deduct the amount from the user's balance
                    user_wallet_obj.balance -=  transfer_data.amount
                    print(user_wallet_obj.balance)
                    # Add the amount to the recipient's balance
                    e_txn = ExternalTransection(
                        user_id=transfer_data.user_id,
                        txdid=str(int(time.time())),
                        txdtype=transfer_data.txdtype,
                        txdrecever=transfer_data.recipientfullname,
                        amount=transfer_data.amount,
                        txdfee=transfer_data.txdfee,
                        totalamount=transfer_data.amount - transfer_data.txdfee,
                        txdcurrency=transfer_data.txdcurrency,
                        recipientfullname=transfer_data.recipientfullname,
                        recipientemail=transfer_data.recipientemail,
                        recipientmobile=transfer_data.recipientmobile,
                        recipientbanktransfer=transfer_data.recipientbanktransfer,
                        recipientbankname=transfer_data.recipientbankname,
                        recipientbankaccountno=transfer_data.recipientbankaccountno,
                        recipientbankswiftcode=transfer_data.recipientbankifsc,
                        recipientaddress=transfer_data.recipientaddress,
                        recipientcurrency =transfer_data.recipientcurrency,
                        )
                    session.add(user_wallet_obj)
                    session.add(e_txn)
                    # session.add(recipient_wallet_obj)
                    await session.commit()
                    return json({'msg': 'External Transfer successful But bank API is not here'},200)
                else:
                    return json({'msg': 'Insufficient balance'},400)
        except SQLAlchemyError as e:
            return json({"Error": str(e)}, 500)