from blacksheep.server.controllers import APIController
from database.db import AsyncSession, async_engine
from blacksheep import pretty_json, Request
from Models.models2 import MerchantPIPE, PIPE, MerchantProdTransaction
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
        """
            This function retrieves merchant pipes data based on a given public key and returns it in a JSON format.<br/><br/>

            Note: The public key is used to identify the merchant in the request.<br/><br/>

            Parameters:<br/>
               - request(Request): The HTTP request object.<br/>
               - schema(PGMerchantPipeCheckoutSchema): The schema object representing the input data expected in the request body.<br/><br/>
                
            Returns:<br/>
             - success (bool): A boolean indicating the success of the operation.<br/>
             - data (list): A list of dictionaries, each representing a merchant pipe.<br/>
             - msg (str, optional): An error message if any exceptions occur during the execution.<br/>
             - msg (str, optional): A message describing the outcome of the operation.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:

                ### Get the payload data
                merchant_public_key_schema = schema.merchant_public_key
                transaction_id             = schema.transaction_id

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
                
                #### Check the transaction has been Failed or not 
                ###################################################
                
                ### Get the transaction of the user
                merchant_prod_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(
                        MerchantProdTransaction.transaction_id == transaction_id,
                        MerchantProdTransaction.merchant_id    == merchant_id
                        )
                ))
                merchant_prod_transaction = merchant_prod_transaction_obj.scalar()

                if not merchant_prod_transaction:
                        return json({'error': 'Invalid Transaction'}, 404)
                
                if merchant_prod_transaction.status == 'PAYMENT_FAILED':
                    return pretty_json({'error': 'Transaction failed'}, 400)
                
                ########################################################################

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

                            # for type in pipe_types:
                            combined_data.append({
                                'pipe_name': pipe_data.name,
                                'payment_medium': pipe_data.payment_medium,
                                'payment_currency': currency.name,
                                # 'pipe_type': type.name
                            })
                        
                except Exception as e:
                    return pretty_json({'msg': 'Merchant data fetch error', 'error': f'{str(e)}'}, 400)
                
                return pretty_json({'msg': 'Success', 'data': combined_data}, 200)

        except Exception as e:
            return pretty_json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)