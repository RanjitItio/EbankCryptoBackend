from blacksheep import json, Request, get, post, put, delete
from database.db import AsyncSession, async_engine
from blacksheep.server.authorization import auth
from Models.models2 import MerchantPIPE, PIPE
from Models.models import Users, Currency
from Models.Admin.PIPE.pipeschema import (
    AdminMerchantPipeAssignSchema, AdminMerchantPipeUdateSchema
    )
from sqlmodel import select, and_



# Assign pipe to Merchant
@auth('userauth')
@post('/api/admin/merchant/pipe/assign/')
async def assign_merchant_pipe(request: Request, schema:  AdminMerchantPipeAssignSchema):
    try:
        async with AsyncSession(async_engine) as session:
            adminIdentity = request.identity
            adminID       = adminIdentity.claims.get('user_id') if adminIdentity else None

            merchant_id = schema.merchant_id
            pipe_id     = schema.pipe_id
            fee         = schema.fee
            status      = schema.status

            #Admin Authentication
            try:
                is_admin_check_obj = await session.execute(select(Users).where(
                    Users.id == adminID
                ))
                is_admin_check = is_admin_check_obj.scalar()
                
                is_admin = is_admin_check.is_admin

                if not is_admin:
                    return json({'msg': 'Admin authentication failed'}, 401)
                
            except Exception as e:
                return json({'msg': 'Admin check error', 'error': f'{str(e)}'}, 400)
            #Admin authentication Ends

            # Check the requested pipe id exists or not
            try:
                pipe_obj = await session.execute(select(PIPE).where(
                    PIPE.id == pipe_id
                ))
                pipe_ = pipe_obj.scalar()

                if not pipe_:
                    return json({'msg': 'Requested pipe id does not exists'}, 404)
                
            except Exception as e:
                return json({'msg': 'Pipe fetch error', 'error': f'{str(e)}'}, 400)
            
            # Check the user exists or not
            try:
                merchant_obj = await session.execute(select(Users).where(
                    Users.id == merchant_id
                ))
                merchant_ = merchant_obj.scalar()

                if not merchant_:
                    return json({'msg': 'Merchant not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'Merchant fetch error', 'error': f'{str(e)}'}, 400)
            
            # Check whether the pipe already assigned to the merchant or Not
            try:
                check_merchant_pipe_obj = await session.execute(select(MerchantPIPE).where(
                    and_(MerchantPIPE.pipe == pipe_.id, MerchantPIPE.merchant == merchant_.id)
                ))
                check_merchant_pipe_ = check_merchant_pipe_obj.scalar()

                if check_merchant_pipe_:
                    return json({'msg': 'Merchant pipe already exists'}, 405)
                
            except Exception as e:
                return json({'msg': 'Merchant pipe check error', 'error': f'{str(e)}'}, 400)
            

            # Assign pipe to merchant
            merchant_pipe = MerchantPIPE(
                pipe      = pipe_.id,
                merchant  = merchant_.id,
                fee       = fee,
                is_active = status   
            )

            session.add(merchant_pipe)
            await session.commit()
            await session.refresh(merchant_pipe)
        
            return json({'msg': 'Assigned successfully'}, 201)
        
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)



# Update assigned pipe details of Merchant
@auth('userauth')
@put('/api/admin/merchant/pipe/update/')
async def update_merchant_pipe(request: Request, schema:  AdminMerchantPipeUdateSchema):
    try:
        async with AsyncSession(async_engine) as session:
            adminIdentity = request.identity
            adminID       = adminIdentity.claims.get('user_id') if adminIdentity else None
          
            # Admin Authentication
            try:
                is_admin_check_obj = await session.execute(select(Users).where(
                    Users.id == adminID
                ))
                is_admin_check = is_admin_check_obj.scalar()
                
                is_admin = is_admin_check.is_admin

                if not is_admin:
                    return json({'msg': 'Admin authentication failed'}, 401)
                
            except Exception as e:
                return json({'msg': 'Admin check error', 'error': f'{str(e)}'}, 400)
            # Admin authentication Ends

            merchant_id   = schema.merchant_id
            pipe_id       = schema.pipe_id
            fee           = schema.fee
            status        = schema.status
            merch_pipe_id = schema.merchant_pipe_id
            coolingPeriod = schema.cooling_period

            # Get The requested pipe
            try:
                pipe_obj = await session.execute(select(PIPE).where(
                    PIPE.id == pipe_id
                ))
                pipe_ = pipe_obj.scalar()

                if not pipe_:
                    return json({'msg': 'Requested pipe id does not exists'}, 404)
                
            except Exception as e:
                return json({'msg': 'Pipe fetch error', 'error': f'{str(e)}'}, 400)
            
            # Get the requested user
            try:
                merchant_obj = await session.execute(select(Users).where(
                    Users.id == merchant_id
                ))
                merchant_ = merchant_obj.scalar()

                if not merchant_:
                    return json({'msg': 'Merchant not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'Merchant fetch error', 'error': f'{str(e)}'}, 400)
            

            # Get the Merchant pipe
            try:
                merchant_pipe_obj = await session.execute(select(MerchantPIPE).where(
                      MerchantPIPE.id == merch_pipe_id
                ))
                merchant_pipe = merchant_pipe_obj.scalar()

                if not merchant_pipe:
                    return json({'msg': 'Requested merchant pipe does not exists'}, 404)

            except Exception as e:
                return json({'msg': 'Merchant pipe fetch error', 'error': f'{str(e)}'}, 400)
            
            
            # Check the Merchant pipe already exists for the user or not
            try:
                merchant_pipe_check_obj = await session.execute(select(MerchantPIPE).where(
                      and_(MerchantPIPE.pipe == pipe_.id, MerchantPIPE.merchant == merchant_.id)
                ))
                merchant_pipe_check = merchant_pipe_check_obj.scalar()

                if merchant_pipe_check:
                    if merchant_pipe_check.id != merchant_pipe.id:
                        return json({'msg': 'Pipe already assigned'}, 405)

            except Exception as e:
                return json({'msg': 'Merchant pipe check error', 'error': f'{str(e)}'}, 400)
            
            merchant_pipe.pipe      = pipe_.id
            merchant_pipe.merchant  = merchant_.id
            merchant_pipe.fee       = fee
            merchant_pipe.is_active = status
            pipe_.settlement_period = coolingPeriod

            session.add(merchant_pipe)
            session.add(pipe_)
            await session.commit()
            await session.refresh(merchant_pipe)
            await session.refresh(pipe_)

            return json({'msg': 'Updated successfully'}, 200)
        
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)



# View all Merchant assigned pipes
@auth('userauth')
@get('/api/admin/merchant/pipes/')
async def list_all_merchant_assigned_pipes(request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            adminIdentity = request.identity
            adminID       = adminIdentity.claims.get('user_id') if adminIdentity else None

            # Admin Authentication
            try:
                is_admin_check_obj = await session.execute(select(Users).where(
                    Users.id == adminID
                ))
                is_admin_check = is_admin_check_obj.scalar()
                
                is_admin = is_admin_check.is_admin

                if not is_admin:
                    return json({'msg': 'Admin authentication failed'}, 401)
                
            except Exception as e:
                return json({'msg': 'Admin check error', 'error': f'{str(e)}'}, 400)
            # Admin authentication Ends

            # Get all the assigned Merchant pipes
            try:
                merchant_pipe_obj = await session.execute(select(MerchantPIPE))
                merchant_pipe_    = merchant_pipe_obj.scalars().all()
            except Exception as e:
                return json({'msg': 'Merchant pipe fetch error', 'error': f'{str(e)}'}, 400)

            return json({'msg': 'fetched_successfully', 'merchant_pipe_data': merchant_pipe_})

    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)




# View all pipes Merchant wise 
@auth('userauth')
@get('/api/admin/merchant/pipe/{id}/')
async def list_all_merchant_wise_pipes(request: Request, id: int):
    try:
        async with AsyncSession(async_engine) as session:
            adminIdentity = request.identity
            adminID       = adminIdentity.claims.get('user_id') if adminIdentity else None
            combined_data = []

            # Admin Authentication
            try:
                is_admin_check_obj = await session.execute(select(Users).where(
                    Users.id == adminID
                ))
                is_admin_check = is_admin_check_obj.scalar()
                
                is_admin = is_admin_check.is_admin

                if not is_admin:
                    return json({'msg': 'Admin authentication failed'}, 401)
                
            except Exception as e:
                return json({'msg': 'Admin check error', 'error': f'{str(e)}'}, 400)
            # Admin authentication Ends


            try:
                stmt = (
                    select(MerchantPIPE, PIPE, Users, Currency)
                    .join(PIPE, MerchantPIPE.pipe == PIPE.id)
                    .join(Users, MerchantPIPE.merchant == Users.id)
                    .join(Currency, PIPE.process_curr == Currency.id)
                    .where(MerchantPIPE.merchant == id)
                )

                result = await session.execute(stmt)
                merchant_pipes = result.fetchall()

                if not merchant_pipes:
                    return json({'msg': 'Merchant pipe does not exist'}, 404)
                
            except Exception as e:
                return json({'msg': 'Merchant pipe fetch error', 'error': f'{str(e)}'}, 400)
            

            for merchantpipe, pipe_data, merchant_data, currency_data in merchant_pipes:
                combined_data.append({
                    'pipe_id':          pipe_data.id,
                    'pipe_name':        pipe_data.name,
                    'merchant_name':    merchant_data.full_name,
                    'merchant_id':      merchant_data.id,
                    'date_assigned':    merchantpipe.assigned_on,
                    'process_mode':     pipe_data.process_mode,
                    'currency':         currency_data.name,
                    'status':           merchantpipe.is_active,
                    'fee':              merchantpipe.fee,
                    'merchant_pipe_id': merchantpipe.id,
                    'settlement_period': pipe_data.settlement_period
                })

            return json({'msg': 'fetched_successfully', 'merchant_pipes': combined_data}, 200)

    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)

