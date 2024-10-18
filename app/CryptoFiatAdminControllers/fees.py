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

