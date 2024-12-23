from blacksheep import Request, json
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from app.controllers.controllers import get, post
from app.generateID import generate_new_button_id
from Models.PG.schema import CreateNewPaymentButtonSchema
from Models.models3 import MerchantPaymentButtonStyles, MerchantPaymentButton
from Models.models import UserKeys
from Models.models2 import MerchantProdTransaction
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_






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
            'white':   '#FFFFFF',
            'dark':    '#0A0D54'
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
        """
            Fetch the button styles for a specific merchant payment button.<br /><br />

            Parameters:<br />
            - request (Request): The request object containing information about the HTTP request.<br />
            - id (str): The unique identifier of the merchant payment button.<br /><br />

            Returns:<br />
            - json: A JSON response containing the button styles or an error message.<br />
    """
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
                    "buttonColor":   self.get_color_codes(button_styles.buttonBgColor),
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
        """
            This function handles the creation of a new payment button for a merchant.<br/><br/>
            
            The payload data should include the following fields:<br/>
            - buttonTitle: The title of the payment button.<br/>
            - buttonLabel: The label of the payment button.<br/>
            - buttonColor: The color of the payment button.<br/>
            - buttonBGColor: The background color of the payment button.<br/>
            - businessName: The name of the business.<br/>
            - redirectUrl: The URL to redirect the user after the payment is completed.<br/>
            - isFixedAmount: A boolean indicating whether the payment amount is fixed.<br/>
            - fixedAmountLabel: The label for the fixed payment amount.<br/>
            - fixedAmount: The fixed payment amount.<br/>
            - fixedAmountCurrency: The currency of the fixed payment amount.<br/>
            - isCustomerAmount: A boolean indicating whether the payment amount is a customer-defined amount.<br/>
            - customerAmountLabel: The label for the customer-defined payment amount.<br/>
            - customerAmount: The customer-defined payment amount.<br/><br/>

            Parameters:<br/>
            - request (Request): The request object containing the user's identity and payload data.<br/>
            - schema (CreateNewPaymentButtonSchema): The schema object containing the validated payload data.<br/><br/>

            Returns:<br/>
            - JSON response with success status, message, and button ID if successful.<br/>
            - JSON response with error status and message if an exception occurs.<br/>
        """
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

                redirectURL         = schema.redirectUrl

                isFixedAmount       = schema.isFixedAmount
                fixedAmountLabel    = schema.fixedAmountLabel
                fixedAmount         = schema.fixedAmount
                fixedAmountCurrency = schema.fixedAmtCurr

                isCustomerAmount    = schema.isCustomerAmt
                customerAmountLabel = schema.customerAmountLabel
                customerAmount      = schema.customerAmount
                customerAmtCurrency = schema.customerAmtCurr

                customerEmailLabel  = schema.customerEmailLabel
                customerPhoneLabel  = schema.customerPhoneLabel

                # Generate new unique ID
                uniqueButtonID = await generate_new_button_id()

                merchantButton = MerchantPaymentButton(
                    merchant_id         = user_id,
                    button_id           = uniqueButtonID,
                    button_title        = buttonTitle,
                    businessName        = businessName,

                    redirectURL         = redirectURL,

                    isFixedAmount       = isFixedAmount,
                    fixedAmountLabel    = fixedAmountLabel,
                    fixedAmount         = fixedAmount,
                    fixedAmountCurrency = fixedAmountCurrency,

                    isCustomerAmount    = isCustomerAmount,
                    customerAmountLabel = customerAmountLabel,
                    customerAmount      = customerAmount,
                    customerAmountCurrency = customerAmtCurrency,

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
        """
        This function retrieves all payment buttons created by a user. It fetches the buttons,
        calculates the total sales made through each button, and returns the data in a structured format.<br/><br/>

        Parameters:<br/>
        - request (Request): The incoming request object containing user identity and other relevant data.<br/><br/>

        Returns:<br/>
        - JSON response containing success status, error message (if any), and the list of payment buttons.<br/>
          The payment buttons are represented as a list of dictionaries, each containing detailed information
          about the button, such as button ID, title, currency, total sales, and status.<br/><br/>

        Raises:<br/>
        - Exception: If any error occurs during the database operations or processing.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                combined_data = []

                # Get the buttons
                payment_button_obj = await session.execute(select(MerchantPaymentButton).where(
                    MerchantPaymentButton.merchant_id == user_id
                ))
                payment_button_ = payment_button_obj.scalars().all()

                if not payment_button_:
                    return json({'error': 'Button Not found'}, 404)
                
                transaction_amount = 0

                for button in payment_button_:
                    # Get success transactions made through the button without refunded
                    merchantButtonTransactionObj = await session.execute(select(MerchantProdTransaction).where(
                        and_(
                            MerchantProdTransaction.merchantOrderId == button.button_id,
                            MerchantProdTransaction.merchant_id     == button.merchant_id,
                            MerchantProdTransaction.is_refunded     == False,
                            MerchantProdTransaction.status          == 'PAYMENT_SUCCESS'
                        )))
                    merchantButtonTransaction = merchantButtonTransactionObj.scalars().all()

                    if merchantButtonTransaction:
                        transaction_amount = sum(transaction.amount for transaction in merchantButtonTransaction)
                    
                    if button.isFixedAmount:
                        selected_currency = button.fixedAmountCurrency
                    elif button.isCustomerAmount:
                        selected_currency = button.customerAmountCurrency
                    else:
                        selected_currency = 'NONE'


                    combined_data.append({
                        'id': button.id,
                        'merchant_id': button.merchant_id,
                        'form_currency': selected_currency,
                        'button_id':  button.button_id,
                        'button_title': button.button_title,
                        'businessName': button.businessName,
                        'isFixedAmount': button.isFixedAmount,
                        'fixedAmountLabel': button.fixedAmountLabel,
                        'fixedAmount': button.fixedAmount,
                        'fixedAmountCurrency': button.fixedAmountCurrency,
                        'isCustomerAmount': button.isCustomerAmount,
                        'customerAmountLabel': button.customerAmountLabel,
                        'customerAmount': button.customerAmount,
                        'customerAmountCurrency': button.customerAmountCurrency,
                        'emailLabel': button.emailLabel,
                        'phoneNoLable': button.phoneNoLable,
                        'cretedAt': button.cretedAt,
                        'total_sales': transaction_amount if transaction_amount else 0,
                        'status': button.is_active,
                    })

                    transaction_amount = 0

                return json({'success': True, 'merchant_payment_buttons': combined_data}, 200)
            
        except Exception as e:
            return json({'error': 'Server error', 'message': f'{str(e)}'}, 500)
        



# All Form fields selected by merchant during button creation
class AllMerchantSelectedFormFields(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Selcted Form Fields'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/merchant/payment/form/fields/'
    
    @get()
    async def get_merchantFormField(self, request: Request, form_id: str):
        try:
            async with AsyncSession(async_engine) as session:
                formID = form_id

                # Get merchant created form
                merchant_form_obj = await session.execute(select(MerchantPaymentButton).where(
                    MerchantPaymentButton.button_id == formID
                ))
                merchant_form_ = merchant_form_obj.scalar()

                if not merchant_form_:
                    return json({'message': 'Payment Button not Found'}, 404)
                
                return json({'success': True, 'merchant_payment_form': merchant_form_}, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)




# Get Merchant Keys using button id
class MerchantKeysFromFormID(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Keys using Form ID'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/merchant/payment/forms/keys/'
    
    
    @get()
    async def get_merchantKeysFromFormID(self, request: Request, form_id: str):
        """
            This function retrieves merchant keys based on a given form ID.<br/><br/>
            
            Parameters:<br/>
             - request(Request): The HTTP request object providing the request parameters of the request.<br/>
             - form_id(str): The unique identifier of the merchant payment button.<br/><br/>

            Returns:<br/>
             - JSON: A JSON response containing the success message along with the merchant_keys if found, or an 404 error message if the merchant form or keys are not found, or 500 if there is a server error.<br/>
             - Error: A JSON response with an error message with status code 404 if the merchant form or keys are not found, or if there is a server error.<br/>
             - HTTPStatus: 401 Unauthorized if the request is not authenticated or the user does not have necessary permissions.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                formId =  form_id

                # Get the merchant payment button
                merchant_form_obj = await session.execute(select(MerchantPaymentButton).where(
                    MerchantPaymentButton.button_id == formId
                ))
                merchant_form = merchant_form_obj.scalar()

                if not merchant_form:
                    return json({'error': 'Merchant form not found'}, 404)
                
                merchant_id = merchant_form.merchant_id

                # Get The merchant keys
                merchant_keys_obj = await session.execute(select(UserKeys).where(
                    UserKeys.user_id == merchant_id
                ))
                merchant_keys = merchant_keys_obj.scalar()

                if not merchant_keys:
                    return json({'error': 'No Key available'}, 404)
                
                return json({'success': True, 'merchant_keys': merchant_keys}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)