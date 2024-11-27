from blacksheep import Request, json
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from app.controllers.controllers import get
from database.db import AsyncSession, async_engine
from Models.models2 import MerchantSandBoxSteps
from Models.models import BusinessProfile, MerchantBankAccount, UserKeys
from sqlmodel import select




# Check how many steps the user has completed to be able to access production environment
class MerchantSandBoxCompletionSteps(APIController):
    """
        This class handles the retrieval of merchant sandbox completion steps.<br/>
        It checks for the completion of business and bank account setup for a merchant.<br/>
        If both steps are completed, it activates the user keys.<br/> 
    """
    
    @classmethod
    def class_name(cls) -> str:
        return 'Merchant SandBox Steps'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/merchant/sb/steps/'
    

    @auth('userauth')
    @get()
    async def get_merchant_sb_steps(self, request: Request):
        """
            This API Retrieves the merchant sandbox completion steps.<br/><br/>

            Parameters:<br/>
                request (Request): The request object containing user identity and other information.<br/><br/>

            Returns:<br/>
                JSON: A JSON response containing the success status, completion status, and completion business step and bank step.<br/>
                If an exception occurs, a JSON response with an error message is returned.<br/><br/>
                
            Raises:<br/>
            - ValueError: If the input data is not valid.<br/>
            - Exception: If there is an error while executing the SQL queries.<br/>
            - Error 500: 'error': 'Server Error'.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate the user
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                # Check for merchant sandbox steps
                merchant_steps_obj = await session.execute(select(MerchantSandBoxSteps).where(
                    MerchantSandBoxSteps.merchantId == user_id
                ))
                merchant_steps = merchant_steps_obj.scalars().first()

                # If no steps exists
                if not merchant_steps:

                    # Merchant Sandbox step acount
                    merchant_sb_step = MerchantSandBoxSteps(
                        merchantId=user_id,  
                        isBusiness=False,
                        isBank=False
                    )

                    # Check Business exists or not
                    merchant_business_obj = await session.execute(select(BusinessProfile).where(
                        BusinessProfile.user == user_id
                    ))
                    merchant_business = merchant_business_obj.scalars().first()

                    # If merchant have any business
                    if merchant_business:
                        merchant_sb_step.isBusiness = True

                    # Check Bank account exists or not
                    merchant_bank_obj = await session.execute(select(MerchantBankAccount).where(
                        MerchantBankAccount.user == user_id
                    ))
                    merchant_bank = merchant_bank_obj.scalars().first()
                    
                    # If has bank details
                    if merchant_bank:
                        merchant_sb_step.isBank = True

                    # If both steps are completed
                    if merchant_business and merchant_bank:
                        merchant_sb_step.is_completed = True

                        # Activate the user keys
                        user_keys_obj = await session.execute(select(UserKeys).where(
                            UserKeys.user_id == user_id
                        ))
                        user_keys = user_keys_obj.scalar()

                        if user_keys:
                            user_keys.is_active = True

                            session.add(user_keys)
                            await session.commit()
                            await session.refresh(user_keys)

                        
                    # Save into DB
                    session.add(merchant_sb_step)
                    await session.commit()
                    await session.refresh(merchant_sb_step)

                    return json({
                        'success': True,
                        'isCompleted': merchant_sb_step.is_completed,
                        'businessStep': merchant_sb_step.isBusiness,
                        'bankStep': merchant_sb_step.isBank
                    }, 200)
                
                # For any available steps
                else:
                    businessStep = merchant_steps.isBusiness
                    bankStep     = merchant_steps.isBank

                    # Business available check
                    merchant_business_obj = await session.execute(select(BusinessProfile).where(
                        BusinessProfile.user == user_id
                    ))
                    merchant_business = merchant_business_obj.scalars().first()

                    # If business available
                    if merchant_business:
                        merchant_steps.isBusiness = True
                    else:
                        merchant_steps.isBusiness = False

                    # Check Bank account exists or not
                    merchant_bank_obj = await session.execute(select(MerchantBankAccount).where(
                        MerchantBankAccount.user == user_id
                    ))
                    merchant_bank = merchant_bank_obj.scalars().first()

                    # If bank account exists
                    if merchant_bank:
                        merchant_steps.isBank = True
                    else:
                        merchant_steps.isBank = False

                    # If both the steps are completed
                    if businessStep and bankStep:
                        merchant_steps.is_completed = True

                        # Activate the User keys
                        # Get the User keys
                        user_keys_obj = await session.execute(select(UserKeys).where(
                            UserKeys.user_id == user_id
                        ))
                        user_keys = user_keys_obj.scalar()

                        # If keys exists
                        if user_keys:
                            user_keys.is_active = True

                            session.add(user_keys)
                            await session.commit()
                            await session.refresh(user_keys)
                    else: 
                        merchant_steps.is_completed = False


                    # Save into DB
                    session.add(merchant_steps)
                    await session.commit()
                    await session.refresh(merchant_steps)

                    return json({
                        'success': True,
                        'isCompleted': merchant_steps.is_completed,
                        'businessStep': merchant_steps.isBusiness,
                        'bankStep': merchant_steps.isBank
                    }, 200)
                
                
        except Exception as e:
            return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)


