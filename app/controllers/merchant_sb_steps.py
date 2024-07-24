from blacksheep import Request, json
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from app.controllers.controllers import get
from database.db import AsyncSession, async_engine
from Models.models2 import MerchantSandBoxSteps
from Models.models import BusinessProfile, MerchantBankAccount
from sqlmodel import select




# Check how many steps the user has completed to be able to access production environment
class MerchantSandBoxCompletionSteps(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant SandBox Steps'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/merchant/sb/steps/'
    

    @auth('userauth')
    @get()
    async def get_merchant_sb_steps(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                merchant_steps_obj = await session.execute(select(MerchantSandBoxSteps).where(
                    MerchantSandBoxSteps.merchantId == user_id
                ))
                merchant_steps = merchant_steps_obj.scalars().first()

                if not merchant_steps:

                    merchant_sb_step = MerchantSandBoxSteps(
                        merchantId=user_id,
                        stepsRemained=2,  
                        isBusiness=False,
                        isBank=False
                    )

                    # Check Business exists or not
                    merchant_business_obj = await session.execute(select(BusinessProfile).where(
                        BusinessProfile.user == user_id
                    ))
                    merchant_business = merchant_business_obj.scalars().first()

                    if merchant_business:
                        merchant_sb_step.isBusiness = True
                        merchant_sb_step.stepsRemained -= 1


                    # Check Bank account exists or not
                    merchant_bank_obj = await session.execute(select(MerchantBankAccount).where(
                        MerchantBankAccount.user == user_id
                    ))
                    merchant_bank = merchant_bank_obj.scalars().first()

                    if merchant_bank:
                        merchant_sb_step.isBank = True
                        merchant_sb_step.stepsRemained -= 1

                    # If both steps are completed
                    if merchant_business and merchant_bank:
                        merchant_sb_step.is_completed = True

                        
                    session.add(merchant_sb_step)
                    await session.commit()
                    await session.refresh(merchant_sb_step)

                    return json({
                        'success': True,
                        'isCompleted': merchant_sb_step.is_completed,
                        'businessStep': merchant_sb_step.isBusiness,
                        'bankStep': merchant_sb_step.isBank
                    }, 200)
                
                else:
                    businessStep = merchant_steps.isBusiness
                    bankStep     = merchant_steps.isBank

                    if businessStep == False:
                        # Check Business exists or not
                        merchant_business_obj = await session.execute(select(BusinessProfile).where(
                            BusinessProfile.user == user_id
                        ))
                        merchant_business = merchant_business_obj.scalars().first()

                        if merchant_business:
                            merchant_steps.isBusiness = True


                    elif bankStep == False:
                        # Check Bank account exists or not
                        merchant_bank_obj = await session.execute(select(MerchantBankAccount).where(
                            MerchantBankAccount.user == user_id
                        ))
                        merchant_bank = merchant_bank_obj.scalars().first()

                        if merchant_bank:
                            merchant_steps.isBank = True

                    if businessStep and bankStep:
                        merchant_steps.is_completed = True

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


