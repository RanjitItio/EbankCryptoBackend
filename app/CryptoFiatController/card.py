from app.controllers.controllers import get, post, put
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from Models.card import FiatCard
from Models.models import Currency
from Models.FIAT.Schema import UserCreateFiatCardSchema, UserUpdateFiatCardSchema, UserUpdateFIATCardPINSchema
from sqlmodel import select, and_, func, desc
from app.generateID import generate_unique_16_digit_number
import random
from datetime import datetime, timedelta




#### Fiat Card Controller(User)
class UserCreateFiatCardController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'User Create Fiat Card Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v7/user/fiat/card/'
    
    
    #### Create new Fiat Card by user
    @auth('userauth')
    @post()
    async def create_fiatCard(self, request: Request, schema: UserCreateFiatCardSchema):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ### Get the payload data
                cardName     = schema.card_name
                cardCurrency = schema.currency

                ### Get the currency 
                currency_obj = await session.execute(select(Currency).where(
                    Currency.name == cardCurrency
                ))
                currency = currency_obj.scalar()

                if not currency:
                    return json({'message': 'Invalid Currency'}, 400)
                
                ### Generate new unique Number
                unique_card_number = await generate_unique_16_digit_number()

                ### Generate New CVV and PIN
                generate_cvv = random.randint(10**2, 10**3 - 1)
                generate_pin = random.randint(10**3, 10**4 - 1)

                ### Card exists
                fiat_card_exist_obj = await session.execute(select(FiatCard).where(
                    and_(
                        FiatCard.currency == currency.id,
                        FiatCard.user_id == user_id
                        )
                ))
                fiat_card_exist = fiat_card_exist_obj.scalar()

                if fiat_card_exist:
                    return json({'message': 'Fiat Card already exists'}, 400)
                

                ### Generate new card
                generate_new_card = FiatCard(
                    user_id     = user_id,
                    card_name   = cardName,
                    card_number = unique_card_number,
                    currency    = currency.id,
                    valid_from  = datetime.now(),
                    valid_thru  = datetime.now() + timedelta(days=500 * 3),
                    cvv         = str(generate_cvv),
                    pin         = str(generate_pin)
                )

                session.add(generate_new_card)
                await session.commit()
                await session.refresh(generate_new_card)

                return json({
                    'success': True,
                    'message': 'Fiat card created successfully'
                }, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        

    
    ### Update FIAT Card
    @auth('userauth')
    @put()
    async def update_fiatCard(self, request: Request, schema: UserUpdateFiatCardSchema):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ### Get the payload data
                cardName = schema.card_name
                cvv      = schema.cvv
                status   = schema.status
                cardId   = schema.card_id

                ### Get the car
                user_fiat_card_obj = await session.execute(select(FiatCard).where(
                    FiatCard.id == cardId
                ))
                user_fiat_card = user_fiat_card_obj.scalar()

                if not user_fiat_card:
                    return json({'message': 'Invalid Card'}, 400)
                
                ### Update the Fiat Card
                user_fiat_card.card_name = cardName
                user_fiat_card.cvv       = cvv
                user_fiat_card.status    = status

                session.add(user_fiat_card)
                await session.commit()
                await session.refresh(user_fiat_card)

                return json({
                    'success': True,
                    'message': 'Card updated successfully'
                }, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        


    #### Get all the card related to a user
    @auth('userauth')
    @get()
    async def get_fiatCard(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ### Get all the cards of the user
                combined_data = []

                stmt = select(
                    FiatCard.id,
                    FiatCard.user_id,
                    FiatCard.card_name,
                    FiatCard.card_number,
                    FiatCard.valid_from,
                    FiatCard.valid_thru,
                    FiatCard.created_at,
                    FiatCard.cvv,
                    FiatCard.pin,
                    FiatCard.status,

                    Currency.name.label('currency')
                ).join(
                    Currency, Currency.id == FiatCard.currency
                ).where(
                    FiatCard.user_id == user_id
                )

                user_fiat_cards_obj = await session.execute(stmt)
                user_fiat_cards = user_fiat_cards_obj.fetchall()

                if not user_fiat_cards:
                    return json({'message': 'No Card found'}, 404)
                
                ### Gather all data
                for card in user_fiat_cards:
                    combined_data.append(
                        {
                            'id': card.id,
                            'user_id': card.user_id,
                            'card_name': card.card_name,
                            'card_number': card.card_number,
                            'valid_from': card.valid_from,
                            'valid_thru': card.valid_thru,
                            'created_at': card.created_at,
                            'cvv': card.cvv,
                            'pin': card.pin,
                            'status': card.status,
                            'currency': card.currency
                        }
                    )

                return json({
                    'success': True,
                    'user_fiat_cards': combined_data
                }, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        



#### Update FIAT Card PIN Controller
class UserUpdateFiatCardPinController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return "Update FIAT Card PIN Controller"
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v7/user/update/fiat/card/pin/'
    
    ### Update FIAT Card PIN
    @auth('userauth')
    @put()
    async def update_fiatCardPIN(self, request: Request, schema: UserUpdateFIATCardPINSchema):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ### Get payload data
                cardID = schema.card_id
                pin    = schema.pin

                ### Get the Fiat Card of user
                user_fiat_card_obj = await session.execute(select(FiatCard).where(
                    and_(
                        FiatCard.user_id == user_id,
                        FiatCard.id  == cardID
                        )
                ))
                user_fiat_card = user_fiat_card_obj.scalar()

                if not user_fiat_card:
                    return json({'message': 'Invalid Card'}, 400)

                if len(pin) > 4:
                    return json({'message': 'Please set four digit pin'}, 400)
                
                ### Uppdate PIN
                user_fiat_card.pin = pin

                session.add(user_fiat_card)
                await session.commit()
                await session.refresh(user_fiat_card)

                return json({
                    'success': True,
                    'message': 'PIN Updated Successfully'
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)