from blacksheep.server.controllers import APIController
from database.db import AsyncSession, async_engine
from blacksheep import pretty_json, Request
from Models.models2 import MerchantPIPE, PIPE, PIPETypeAssociation, PIPEType
from Models.models import UserKeys, Currency
from sqlmodel import select, and_
from Models.PG.schema import PGMerchantPipeCheckoutSchema
from app.controllers.controllers import post
from app.generateID import base64_decode
import json





# Get the available active merchant pipes during checkout
class MerchantPipes(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Available Pipes'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v3/merchant/checkout/pipe/'
    
    @post()
    async def get_merchant_pipes(request: Request, schema: PGMerchantPipeCheckoutSchema):
        try:
            async with AsyncSession(async_engine) as session:
                merchant_public_key_schema = schema.merchant_public_key

                # Decode the key
                merchant_public_key_decode = base64_decode(merchant_public_key_schema)
                # merchant_public_key = base64_decode(merchant_public_key_schema)
                merchant_public_key = json.loads(merchant_public_key_decode)

                combined_data       = []
               
                try:
                    merchant_key_obj = await session.execute(select(UserKeys).where(
                        UserKeys.public_key == merchant_public_key
                    ))
                    merchant_key = merchant_key_obj.scalar()

                    if not merchant_key:
                        return pretty_json({'error': 'Invalid key'}, 400)
                    
                    # Merchant Id
                    merchant_id = merchant_key.user_id
                    
                except Exception as e:
                    return pretty_json({'error': 'Server error', 'error': f'{str(e)}'}, 500)
                

                # Check for active Merchant assigned pipes
                try:
                    mechant_assigned_pipe = await session.execute(select(MerchantPIPE).where(
                        and_(MerchantPIPE.merchant == merchant_id, MerchantPIPE.is_active ==  True)
                    ))
                    merchant_assigned_pipe = mechant_assigned_pipe.scalars().all()

                    if not merchant_assigned_pipe:
                        return pretty_json({'msg': 'No available merchant pipe'}, 404)
                    
                except Exception as e:
                    return pretty_json({'Merchant assigned pipe error'}, 400)


                if not merchant_assigned_pipe:
                    return pretty_json({'error': 'No assigned pipe'}, 400)
                
                # Check those pipes are active or not 
                try:
                    for merchant_pipes in merchant_assigned_pipe:
                        pipe_obj = await session.execute(select(PIPE).where(
                            and_(PIPE.id == merchant_pipes.pipe, PIPE.is_active == True)
                        ))
                        pipes = pipe_obj.scalars().all()

                        if not pipes:
                            return pretty_json({'error': 'No active pipe available'}, 400)
                        
                        for pipe_data in pipes:
                            # Get the related currency
                            currency_obj = await session.execute(select(Currency).where(
                                Currency.id == pipe_data.process_curr
                            ))
                            currency = currency_obj.scalar()

                            # Get all the Associated payment methods
                            # payment_mode_obj = await session.execute(select(PIPETypeAssociation).where(
                            #     PIPETypeAssociation.pipe_id == pipe_data.id  # Correct reference here
                            # ))
                            # payment_modes = payment_mode_obj.scalars().all()

                            # for mode in payment_modes:
                            #     pipe_type_obj = await session.execute(select(PIPEType).where(
                            #         PIPEType.id == mode.pipe_type_id
                            #     ))
                            #     pipe_types = pipe_type_obj.scalars().all()

                            # for type in pipe_types:
                            combined_data.append({
                                'pipe_name': pipe_data.name,
                                'payment_medium': pipe_data.payment_medium,
                                'payment_currency': currency.name,
                                # 'pipe_type': type.name
                            })
                        
                except Exception as e:
                    return pretty_json({'msg': 'Merchant data fetch error', 'error': f'{str(e)}'}, 400)
                
                 # Fetch all necessary data with a join query
                # query = (
                #     select(
                #         PIPE.name.label('pipe_name'),
                #         PIPE.payment_medium,
                #         Currency.name.label('payment_currency'),
                #         PIPEType.name.label('pipe_type')
                #     )
                #     .join(MerchantPIPE, MerchantPIPE.pipe == PIPE.id)
                #     .join(Currency, PIPE.process_curr == Currency.id)
                #     .join(PIPETypeAssociation, PIPETypeAssociation.pipe_id == PIPE.id)
                #     .join(PIPEType, PIPETypeAssociation.pipe_type_id == PIPEType.id)
                #     .where(
                #         MerchantPIPE.merchant == merchant_id,
                #         MerchantPIPE.is_active == True,
                #         PIPE.is_active == True
                #     )
                # )

                # result = await session.execute(query)
                # combined_data = [
                #     {
                #         'pipe_name': row.pipe_name,
                #         'payment_medium': row.payment_medium,
                #         'payment_currency': row.payment_currency,
                #         'pipe_type': row.pipe_type
                #     }
                #     for row in result
                # ]

                return pretty_json({'msg': 'Success', 'data': combined_data}, 200)

        except Exception as e:
            return pretty_json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)