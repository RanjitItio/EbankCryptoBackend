from app.controllers.controllers import get, post, put, delete
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
        """
            Create a new Fiat Card by the user.<br/><br/>

            Parameters:<br/>
                - request: The request object containing user identity and payload data.<br/>
                - schema: The UserCreateFiatCardSchema object containing the card details.<br/><br/>

            Returns:<br/>
                - JSON response with success status and the newly created card details if successful.<br/>
                - JSON response with error status and a message in case of server error.<br/><br/>

            Raises:<br/>
                - JSON response with error status and a message in case of server error.<br/><br/>

            Error message:<br/>
                - 'Fiat Card already exists' if the card is already Exists.<br/>
                - 'Invalid Currency' if the provided currency is not valid.<br/>
        """
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
                    pin         = str(generate_pin),
                    status      = 'Active'
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
        """
            Update the details of an existing Fiat Card.<br/><br/>

            Parameters:<br/>
                - request: The request object containing user identity and payload data.<br/>
                - schema: The UserUpdateFiatCardSchema object containing the card details.<br/><br/>

            Returns:<br/>
                - JSON response with success status and the updated card details if successful.<br/>
                - JSON response with error status and a message in case of server error.<br/><br/>

            Raises:<br/>
                - JSON response with error status and a message in case of server error.<br/><br/>

            Error message:<br/>
                - 'Invalid Card' if the provided card ID is not valid.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ### Get the payload data
                cardName = schema.card_name
                status   = schema.status
                cardId   = schema.card_id

                ### Get the car
                user_fiat_card_obj = await session.execute(select(FiatCard).where(
                    and_(
                        FiatCard.id == cardId,
                        FiatCard.user_id == user_id
                        )
                ))
                user_fiat_card = user_fiat_card_obj.scalar()

                if not user_fiat_card:
                    return json({'message': 'Invalid Card'}, 400)
                
                ### Update the Fiat Card
                if status == 'Active':
                    user_fiat_card.card_name = cardName
                    user_fiat_card.status    = status
                    user_fiat_card.is_active = True

                    session.add(user_fiat_card)

                elif status == 'Inactive':
                    user_fiat_card.card_name = cardName
                    user_fiat_card.status    = status
                    user_fiat_card.is_active = False

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
        """
            Get all the Fiat Cards associated with the user.<br/><br/>

            Parameters:<br/>
                - request: The request object containing user identity.<br/><br/>

            Returns:<br/>
                - JSON response with success status and a list of user's Fiat Cards if successful.<br/>
                - JSON response with error status and a message in case of server error.<br/><br/>

            Raises:<br/>
                - JSON response with error status and a message in case of server error.<br/><br/>

            Error message:<br/>
                - 'No Card found' if the user does not have any Fiat Cards.<br/>
        """
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
        

    #### Delete card
    @auth('userauth')
    @delete()
    async def delete_UserFiatCard(self, request: Request, card_id: int):
        """
            Delete a specific Fiat Card associated with the user.<br/><br/>

            Parameters:<br/>
                - request: The request object containing user identity.<br/>
                - card_id: The ID of the Fiat Card to be deleted.<br/><br/>

            Returns:<br/>
                - JSON response with success status and a message indicating successful deletion if successful.<br/>
                - JSON response with error status and a message in case of server error.<br/><br/>

            Raises:<br/>
                - JSON response with error status and a message in case of server error.<br/><br/>

            Error message:<br/>
                - 'Invalid Card' if the provided card ID is not valid.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                #### Get the Fiat card of the user
                user_fiat_card_obj = await session.execute(select(FiatCard).where(
                    and_(
                        FiatCard.id == card_id,
                        FiatCard.user_id == user_id
                        )
                ))
                user_fiat_card = user_fiat_card_obj.scalar()

                if not user_fiat_card:
                    return json({'message': 'Invalid Card'}, 400)
                
                await session.delete(user_fiat_card)
                await session.commit()

                return json({
                    'success': True,
                    'message': 'Card deleted successfully'
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
        """
            This function updates the PIN of a Fiat Card of a user.<br/>
            It verifies the user's identity, checks the validity of the card, and updates the PIN.<br/><br/>

            Parameters:<br/>
                - request (Request): The request object containing the user's identity and payload data.<br/>
                - schema (UserUpdateFIATCardPINSchema): The schema object containing the card ID and PIN.<br/><br/>

            Returns:<br/>
                - JSON response with success status, message, or error details.<br/>
                    - On success: {'success': True,'message': 'PIN Updated Successfully'}<br/>
                    - On failure: {'message': 'Error message'} with appropriate HTTP status code.<br/><br/>

            Raises:<br/>
                - Exception: If any error occurs during the operation, it is caught and a JSON response with an appropriate error message is returned.<br/><br/>

            Error Messages:<br/>
                - ValueError: If the payload data is invalid.<br/>
                - Error 400: 'Invalid Card' or 'Please set four digit pin' if the card ID or PIN is invalid.<br/>
                - Error 500: 'Server Error' if any other error occurs.<br/>
        """
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