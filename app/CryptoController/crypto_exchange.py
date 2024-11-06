from app.controllers.controllers import get, post, put
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from sqlmodel import select, desc, func, and_
from sqlalchemy.orm import aliased
from database.db import AsyncSession, async_engine
from Models.crypto import CryptoExchange, CryptoWallet
from Models.models import Wallet
from Models.fee import FeeStructure
from Models.Crypto.schema import UserCreateCryptoExchangeSchema
from app.generateID import generate_new_crypto_exchange_transaction_id
from app.CryptoController.calculateFee import CalculateFee



### User Crypto Exchange controller
class UserCryptoExchangeController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'User Crypto Exchange Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/user/crypto/exchange/'
    

    ### Create new Crypto Exchange Transaction for user
    @auth('userauth')
    @post()
    async def create_cryptoExchange(self, request: Request, schema: UserCreateCryptoExchangeSchema):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ### Get the payload data
                cryptoWalletID  = schema.crypto_wallet_id
                fiatWalletID    = schema.fiat_wallet_id
                exchangeAmount  = schema.exchange_amount
                convertedAmount = schema.converted_amount

                ## Get the user Crypto Wallet
                user_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                   and_(
                       CryptoWallet.id == cryptoWalletID,
                       CryptoWallet.user_id == user_id
                       )
                ))
                user_crypto_wallet = user_crypto_wallet_obj.scalar()

                if not user_crypto_wallet:
                    return json({'message': 'Invalid Crypto Wallet'}, 404)
                
                ## Get the fiat Wallet
                user_fiat_wallet_obj = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.id      == fiatWalletID,
                        Wallet.user_id == user_id
                    )
                ))
                user_fiat_wallet = user_fiat_wallet_obj.scalar()

                if not user_fiat_wallet:
                    return json({'message': 'Invalid FIAT Wallet'}, 404)
                
                ## Crypto Wallet balance validation
                if user_crypto_wallet.balance < float(exchangeAmount if exchangeAmount else 0):
                    return json({'message': 'Insufficient balance in Account'}, 400)
                
                # Get fee for Exchange Crypto
                crypto_exchange_fee_obj = await session.execute(select(FeeStructure).where(
                    FeeStructure.name == 'Crypto Exchange'
                ))
                crypto_exchange_fee = crypto_exchange_fee_obj.scalar()

                exchange_transaction_id = await generate_new_crypto_exchange_transaction_id()

                if crypto_exchange_fee:
                    float_qty      = float(exchangeAmount)
                    calculated_fee = await CalculateFee(crypto_exchange_fee.id, float_qty)

                    create_crypto_exchange_transaction = CryptoExchange(
                            user_id                = user_id,
                            transaction_id         = exchange_transaction_id,
                            crypto_wallet          = user_crypto_wallet.id,
                            fiat_wallet            = user_fiat_wallet.id,
                            exchange_crypto_amount = float(exchangeAmount),
                            converted_fiat_amount  = float(convertedAmount),
                            status                 = 'Pending',
                            fee_value              = float(calculated_fee)
                    )

                    session.add(create_crypto_exchange_transaction)

                else:
                    calculated_fee = 10

                    create_crypto_exchange_transaction = CryptoExchange(
                            user_id                = user_id,
                            transaction_id         = exchange_transaction_id,
                            crypto_wallet          = user_crypto_wallet.id,
                            fiat_wallet            = user_fiat_wallet.id,
                            exchange_crypto_amount = float(exchangeAmount),
                            converted_fiat_amount  = float(convertedAmount),
                            status                 = 'Pending',
                            fee_value              = float(calculated_fee)
                    )

                    session.add(create_crypto_exchange_transaction)

                await session.commit()
                await session.refresh(create_crypto_exchange_transaction)

                return json({
                    'success': True,
                    'message': 'Transaction Created Successfully'
                    }, 200)
            
        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)
        
    
    ### Get all Crypto Exchange of the user
    @auth('userauth')
    @get()
    async def get_cryptoExchange(self, request: Request, limit: int = 10, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                combined_data = []

                ### Count all availble rows for paginated data
                select_rows  = select(func.count(CryptoExchange.id)).where(CryptoExchange.user_id == user_id)
                execute_quey = await session.execute(select_rows)

                total_rows = execute_quey.scalar()

                paginated_rows = total_rows / limit

                ## Select the data
                stmt = select(
                    CryptoExchange.id,
                    CryptoExchange.user_id,
                    CryptoExchange.transaction_id,
                    CryptoExchange.created_at,
                    CryptoExchange.exchange_crypto_amount,
                    CryptoExchange.converted_fiat_amount,
                    CryptoExchange.status,
                    CryptoExchange.fee_value,

                    CryptoWallet.crypto_name,
                    Wallet.currency,
                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoExchange.crypto_wallet
                ).join(
                    Wallet, Wallet.id == CryptoExchange.fiat_wallet
                ).where(
                    CryptoExchange.user_id == user_id
                ).order_by(
                    desc(CryptoExchange.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                all_crypto_exchange_transaction_obj = await session.execute(stmt)
                all_crypto_exchange_transaction     = all_crypto_exchange_transaction_obj.fetchall()

                for transaction in all_crypto_exchange_transaction:

                    combined_data.append({
                        'id': transaction.id,
                        'user_id': transaction.user_id,
                        'transaction_id': transaction.transaction_id,
                        'created_at': transaction.created_at,
                        'exchange_crypto_amount': transaction.exchange_crypto_amount,
                        'converted_fiat_amount': transaction.converted_fiat_amount,
                        'status': transaction.status,
                        'fee_value': transaction.fee_value,
                        'crypto_name': transaction.crypto_name,
                        'fiat_currency': transaction.currency
                    })


                return json({
                    'success': True,
                    'user_crypto_exchange_data': combined_data,
                    'paginated_rows': paginated_rows
                }, 200)


        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)