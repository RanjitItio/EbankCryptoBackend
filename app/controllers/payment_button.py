from blacksheep import Request, json
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from app.controllers.controllers import get, post
from app.generateID import generate_new_button_id
from Models.PG.schema import CreateNewPaymentButtonSchema
from Models.models3 import MerchantPaymentButtonStyles, MerchantPaymentButton
from database.db import AsyncSession, async_engine
from sqlmodel import select




# Get The merchant button styles
class PaymentButtonStyle(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Button Styles'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/merchant/payment/fetch/button/'
    
    def get_bg_color_codes(self, color):
        color_codes = {
            'blue':    '#2196f3',
            'light':   'white',
            'outline': 'transparent',
            'aqua':    '#00BFFF',
            'white':   '#FFFFFF'
        }
        return color_codes.get(color, 'white')
    
    def get_color_codes(self, color):
        color_codes = {
            'dark':    '#FFFFFF',
            'blue':    'white',
            'light':   'black',
            'aqua':    '#FFFFFF',
            'white':   'black'
        }
        return color_codes.get(color, 'black')
    

    @get()
    async def get_button_styles(self, request: Request, id: str):
        try:
            async with AsyncSession(async_engine) as session:

                button_data = []

                buttonID = id
                # Get the merchant's button style
                button_style_obj = await session.execute(select(MerchantPaymentButtonStyles).where(
                    MerchantPaymentButtonStyles.button_id == buttonID
                ))
                button_styles = button_style_obj.scalar()

                if not button_styles:
                    return json({'error': 'Incorrect Button ID'}, 404)
                

                button_data.append({
                    "id": button_styles.id,
                    "buttonLabel":   button_styles.buttonLabel,
                    "buttonColor":   self.get_color_codes(button_styles.buttonColor),
                    "buttonBgColor": self.get_bg_color_codes(button_styles.buttonBgColor),
                    "button_id":     button_styles.button_id
                })

                return json({'success': True, 'data': button_data}, 200)
            
        except Exception as e:
            return json({'error': 'Server error', 'message': f'{str(e)}'}, 500)




# Create new payment Button
class CreateMerchantPaymentButton(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Create Payment Button'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/merchant/payment/button/'
    
    @auth('userauth')
    @post()
    async def create_paymentButton(self, request: Request, schema: CreateNewPaymentButtonSchema):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                # All the data contain in Request payload
                buttonTitle         = schema.buttonTitle
                buttonLabel         = schema.buttonLabel
                buttonColor         = schema.buttonColor
                buttonBgColor       = schema.buttonBGColor
                businessName        = schema.businessName
                fixedAmountLabel    = schema.fixedAmountLabel
                fixedAmount         = schema.fixedAmount
                customerAmountLabel = schema.customerAmountLabel
                customerAmount      = schema.customerAmount
                customerEmailLabel  = schema.customerEmailLabel
                customerPhoneLabel  = schema.customerPhoneLabel

                # Generate new unique ID
                uniqueButtonID = await generate_new_button_id()

                merchantButton = MerchantPaymentButton(
                    merchant_id         = user_id,
                    button_id           = uniqueButtonID,
                    button_title        = buttonTitle,
                    businessName        = businessName,
                    fixedAmountLabel    = fixedAmountLabel,
                    fixedAmount         = fixedAmount,
                    customerAmountLabel = customerAmountLabel,
                    customerAmount      = customerAmount,
                    emailLabel          = customerEmailLabel,
                    phoneNoLable        = customerPhoneLabel
                )

                session.add(merchantButton)
                await session.commit()
                await session.refresh(merchantButton)

                button_styles = MerchantPaymentButtonStyles(
                    button_id     = merchantButton.button_id,
                    buttonLabel   = buttonLabel,
                    buttonColor   = buttonColor,
                    buttonBgColor = buttonBgColor
                )

                session.add(button_styles)
                await session.commit()
                await session.refresh(button_styles)

                return json({
                    'success': True, 
                    'message': 'Button created successfully', 
                    'buttonID': uniqueButtonID}, 
                    200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)

    
    # Get all payment button created by the user
    @auth('userauth')
    @get()
    async def get_payment_buttons(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                # Get the buttons
                payment_button_obj = await session.execute(select(MerchantPaymentButton).where(
                    MerchantPaymentButton.merchant_id == user_id
                ))
                payment_button_ = payment_button_obj.scalars().all()

                if not payment_button_:
                    return json({'error': 'Button Not found'}, 404)
                
                return json({'success': True, 'merchant_payment_buttons': payment_button_}, 200)
            
        except Exception as e:
            return json({'error': 'Server error', 'message': f'{str(e)}'}, 500)