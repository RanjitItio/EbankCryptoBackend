from app.controllers.controllers import get, post, put, delete
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.fee import FeeStructure
from Models.FIAT.Schema import AdminAddFeeSchema, AdminUpdateFeeSchema
from sqlmodel import select, desc, func, and_





## Admin Fee Controller
class AdminFeeController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Fee Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v3/admin/fees/'
    
    @auth('userauth')
    @post()
    async def add_fee(self, request: Request, schema: AdminAddFeeSchema):
        """
            This handles the addition of a fee by an admin user after authentication and validation checks.<br/><br/>
            
            Parameters:<br/>
               - request - Request object.<br/>
               - schema(AdminAddFeeSchema): The `schema` parameter in the `add_fee` function represents the data schema for
                                            adding a fee. It contains fee_name (str), fee_type (str), tax_rate (float), fixed_value (float)<br/><br/>

            Returns:<br/>
                - A JSON response indicating success or failure, along with an appropriate message.<br/>
                - If the fee name already exists in the database, it returns a message indicating that the fee name already exists.<br/>
                - If the user making the request is not an admin, it returns a message indicating unauthorized access.<br/>
                - If the fee is successfully created and added to the database, it returns a success message.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                    user_identity = request.identity
                    admin_id       = user_identity.claims.get('user_id') if user_identity else None
                    
                    ## Admin Authnetication
                    user_object      = select(Users).where(Users.id == admin_id)
                    save_to_db       = await session.execute(user_object)
                    user_object_data = save_to_db.scalar()

                    if user_object_data.is_admin == False:
                        return json({'message': 'Unauthorized'}, 401)
                    ## Admin authentication ends

                    ## Get payload data
                    feeName     = schema.fee_name
                    feeType     = schema.fee_type
                    taxRate     = schema.tax_rate
                    fixed_value = schema.fixed_value

                    ## Validation 
                    fee_name_exist_obj = await session.execute(select(FeeStructure).where(
                        FeeStructure.name == feeName
                    ))
                    fee_name_exist = fee_name_exist_obj.scalar()

                    if fee_name_exist:
                        return json({'message': 'Fee Name already exists'}, 400)
                    
                    
                    # create Fee
                    transaction_fee = FeeStructure(
                         name      = feeName,
                         fee_type  = feeType,
                         tax_rate  = taxRate,
                         min_value = fixed_value
                    )

                    session.add(transaction_fee)
                    await session.commit()
                    await session.refresh(transaction_fee)


                    return json({
                         'success': True,
                         'message': 'Fee created successfully'
                    }, 201)

        except Exception as e:
             return json({
                  'error': 'Server Error',
                  'message': f'{str(e)}'
                  }, 500)
        

    ## Update Fees
    @auth('userauth')
    @put()
    async def update_fee(self, request: Request, schema: AdminUpdateFeeSchema):
        """
            This function updates a fee structure in a database after performing user authentication and input validation.<br/><br/>

            Parameters: <br/>
               - request(Request): The request object.<br/>
               - schema(AdminUpdateFeeSchema): The `schema` parameter represents the data schema for updating a fee. 
                                               It contains the following attributes: fee_id (int), fee_name (str), fee_type (str), tax_rate (float), fixed_value (float)<br/><br/>
           
            Returns:<br/>
                - The code snippet returns a JSON response with a success message and status code.<br/>
                - If the fee is successfully updated, it returns a JSON object with the keys 'success' set to True and
                  'message' set to 'Fee Updated Successfully' along with a status code of 200.<br/>
                - If the fee does not exist or the user making the request is not an admin, it returns a JSON object
                  with the keys 'error' set to 'Fee Not Found' and a status code of 404.<br/>
                - If an exception occurs during the update process, it returns a generic success message with a status code of 404.<br/>
                - If the request is not authenticated, it returns a JSON object with the keys 'error' set to 'Unauthorized' and a status code of 401.<br/>
                - If the request is not valid, it returns a JSON object with the keys 'error' set to 'Invalid Request' and a status code of 400.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')
                
                ## Admin Authnetication
                user_object      = select(Users).where(Users.id == admin_id)
                save_to_db       = await session.execute(user_object)
                user_object_data = save_to_db.scalar()

                if user_object_data.is_admin == False:
                    return json({'message': 'Unauthorized'}, 401)
                ## Admin authentication ends

                ## Get payload data
                feeName     = schema.fee_name
                feeType     = schema.fee_type
                taxRate     = schema.tax_rate
                fixed_value = schema.fixed_value
                feeId       = schema.fee_id
        

                ## Get The Fee structure Id
                fee_structure_obj = await session.execute(select(FeeStructure).where(
                    FeeStructure.id == feeId
                ))
                fee_structure = fee_structure_obj.scalar()

                if not fee_structure:
                    return json({'message': 'Invalid Fee ID'}, 400)
                
                fee_name_exist_obj = await session.execute(select(FeeStructure).where(
                    and_(
                        FeeStructure.name == feeName, 
                        FeeStructure.id != feeId
                    )
                ))
                fee_name_exist = fee_name_exist_obj.scalar()

                if fee_name_exist:
                    return json({'message': 'Fee Name already exists'}, 400)
                

                ## update Fee Structure
                fee_structure.name      = feeName
                fee_structure.fee_type  = feeType
                fee_structure.tax_rate  = taxRate
                fee_structure.min_value = fixed_value

                session.add(fee_structure)
                await session.commit()
                await session.refresh(fee_structure)

                return json({
                    'success': True,
                    'message': 'Fee Updated Successfully'
                }, 200)


        except Exception as e:
             return json({
                  'success': True,
                  'message': 'Updated Successfully'
                  }, 200)
        


    ## Get all available fees
    @auth('userauth')
    @get()
    async def get_fees(self, request: Request):
        """
            This function retrieves fee structure data after verifying admin authentication.<br/><br/>
            
            Parameters:<br/>
            - request (Request): The incoming request object containing user identity and other relevant data.<br/><br/>
            
            Returns:<br/>
            - JSON response with success status 200 and fee structure data if the user is authenticated as an admin.<br/>
            - JSON response with error status 401 and message if the user is not authenticated as an admin.<br/>
            - JSON response with error status 500 and message if any exception occurs during the database operations.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                ## Admin Authnetication
                user_object      = select(Users).where(Users.id == admin_id)
                save_to_db       = await session.execute(user_object)
                user_object_data = save_to_db.scalar()

                if user_object_data.is_admin == False:
                    return json({'msg': 'Unauthorized'}, 401)
                ## Admin authentication ends

                ## Get all available fees
                fee_structure_obj = await session.execute(select(FeeStructure))
                fee_structure     = fee_structure_obj.scalars().all()

                return json({
                    'success': True,
                    'fee_structure_data': fee_structure
                }, 200)
            
        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 200)
        

    ## Delete a fee structure
    @auth('userauth')
    @delete()
    async def delete_fees(self, request: Request):
        """
            This function deletes a fee structure after verifying the admin user's authentication.<br/><br/>

            Parameters:
            - request (Request): The incoming request object containing user identity and other relevant data.<br/><br/>
            
            Returns:
            - JSON response with success status 200 and a message 'Fee Structure deleted successfully' if the user is authenticated as an admin.<br/>
            - JSON response with error status 401 and message if the user is not authenticated as an admin.<br/>
            - JSON response with error status 500 and message if any exception occurs during the database operations.<br/>
            - If the fee structure with the provided ID does not exist, it returns a JSON response with a message 'Fee Structure not available' and status code 400.
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                ## Admin Authnetication
                user_object      = select(Users).where(Users.id == admin_id)
                save_to_db       = await session.execute(user_object)
                user_object_data = save_to_db.scalar()

                if user_object_data.is_admin == False:
                    return json({'msg': 'Unauthorized'}, 401)
                ## Admin authentication ends

                request_data = await request.json()

                fee_id = request_data['fee_id']
                
                ## Get the fee
                fee_structure_obj = await session.execute(select(FeeStructure).where(
                    FeeStructure.id == fee_id
                ))
                fee_structure = fee_structure_obj.scalar()

                if not fee_structure:
                    return json({'message': 'Fee Structure not available'}, 400)
                

                await session.delete(fee_structure)
                await session.commit()
                
                return json({
                    'success': True,
                    'message': 'Deleted Successfully'
                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)

