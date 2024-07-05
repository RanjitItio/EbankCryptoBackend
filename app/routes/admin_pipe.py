from blacksheep import json, Request, post, put, delete, get
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users, Currency
from Models.models2 import PIPE, PIPEType, PIPETypeAssociation
from sqlmodel import select, or_, and_
from Models.Admin.PIPE.pipeschema import AdminPipeCreateSchema, AdminPipeUpdateSchema



#Create New Pipe by Admin
@auth('userauth')
@post('/api/v5/admin/pipe/new/')
async def Admin_pipe_create(request: Request, schema: AdminPipeCreateSchema):
    try: 
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id') if admin_identity else None

            if admin_id is None:
                return json({'msg': 'Unauthorized'}, 401)
            
            #Authenticate the user as Admin
            try:
                is_admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                is_admin_user = is_admin_user_obj.scalar()

                check_admin = is_admin_user.is_admin

                if not check_admin:
                    return json({'msg': 'Admin authorization failed'}, 403)

            except Exception as e:
                return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            #Admin Authentication ends

            if schema.status == 'Active':
                is_pipe_active = True
            elif schema.status == 'Inactive':
                is_pipe_active = False
            else:
                is_pipe_active = False
            

            #Check the Pipe already exists or not          
            pipe_field_check_obj = await session.execute(select(PIPE).where(
                or_(
                    PIPE.name     == schema.pipe_name,
                    PIPE.test_url == schema.test_url,
                    PIPE.prod_url == schema.prod_url
                )
            ))
            pipe_field_check = pipe_field_check_obj.scalar()

            if pipe_field_check:
                if pipe_field_check.name == schema.pipe_name:
                    return json({'msg': 'Pipe Name already exists'}, 409)
                # elif pipe_field_check.test_url == schema.test_url:
                #     return json({'msg': 'Pipe test url already exists'}, 409)
                # elif pipe_field_check.prod_url == schema.prod_url:
                #     return json({'msg': 'Pipe Prod url already exists'}, 409)
            
            currency_obj = await session.execute(select(Currency).where(
                Currency.id == schema.process_cur
            ))
            currency = currency_obj.scalar()

            if currency:
                currency_id = currency.id

            #Create Pipe
            new_pipe = PIPE(
                name               = schema.pipe_name,
                status             = schema.status,
                is_active          = is_pipe_active,

                # connect_mode       = pipe_conn_mode.id,
                connection_mode    = schema.connect_mode,

                prod_url           = schema.prod_url,
                test_url           = schema.test_url,
                status_url         = schema.status_url,
                refund_url         = schema.refund_url,
                auto_refund        = schema.auto_refnd,
                whitelisting_ip    = schema.white_ip,
                webhook_url        = schema.webhook_url,
                whitelist_domain   = schema.white_domain,
                refund_policy      = schema.refund_pol,

                #Processing Credentials
                headers            = schema.headers,
                body               = schema.body,
                query              = schema.query,
                auth_keys          = schema.auth_keys,

                redirect_msg       = schema.redirect_msg,
                checkout_label     = schema.chkout_lable,
                checkout_sub_label = schema.chkout_sub_lable,
                comments           = schema.cmnt,

                #Processing Mode
                process_mode       = schema.process_mod,

                process_curr       = currency_id,

                settlement_period  = schema.settlement_prd,

                #Bank Response
                bank_max_fail_trans_allowed = schema.bnk_max_fail_trans_alwd,
                bank_down_period            = schema.bnk_dwn_period,
                bank_success_resp           = schema.bnk_sucs_resp,
                bank_fail_resp              = schema.bnk_fl_resp,
                bank_pending_res            = schema.bnk_pndng_res,
                bank_status_path            = schema.bnk_stus_path,

                #Bank Transaction
                bank_min_trans_limit = schema.bnk_min_trans_lmt,
                bank_max_trans_limit = schema.bnk_max_trans_lmt,
                bank_scrub_period    = schema.bnk_scrub_period,
                bank_trxn_count      = schema.bnk_trxn_cnt,
                bank_min_success_cnt = schema.bnk_min_sucs_cnt,
                bank_min_fail_count  = schema.bnk_min_fl_count
            )

            # Assign Active countries to pipe
            if schema.active_cntry:
                active_country = ",".join(schema.active_cntry)
                
                new_pipe.process_country = active_country

            #Assign Block countries to pipe
            if schema.block_cntry:
                block_country = ",".join(schema.block_cntry)

                new_pipe.block_country = block_country


            session.add(new_pipe)
            await session.commit()
            await session.refresh(new_pipe)

            #Assign Pipe types to pipe
            if schema.type:
                schema_pipe_type = schema.type
                for type in schema_pipe_type:
                    pipe_type_obj = await session.execute(select(PIPEType).where(
                        PIPEType.id == type
                    ))
                    pipe_type = pipe_type_obj.scalar()

                    if pipe_type:
                        pipe_type_association = PIPETypeAssociation(
                            pipe_id = new_pipe.id,
                            pipe_type_id = pipe_type.id
                        )

                        session.add(pipe_type_association)

                await session.commit()
                await session.refresh(pipe_type_association)

            return json({'msg': 'Created Successfully'}, 201)
        
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    


#Update Pipe by Admin
@auth('userauth')
@put('/api/v5/admin/pipe/update/')
async def Admin_pipe_update(request: Request, schema: AdminPipeUpdateSchema):
    try: 
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id') if admin_identity else None

            if admin_id is None:
                return json({'msg': 'Unauthorized'}, 401)
            
            #Authenticate the user as Admin
            try:
                is_admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                is_admin_user = is_admin_user_obj.scalar()

                check_admin = is_admin_user.is_admin

                if not check_admin:
                    return json({'msg': 'Admin authorization failed'}, 403)

            except Exception as e:
                return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            #Admin Authentication ends

            if schema.status == 'Active':
                is_pipe_active = True
            elif schema.status == 'Inactive':
                is_pipe_active = False
            else:
                is_pipe_active = False


            #Get the pipe
            try:
                pipe_obj = await session.execute(select(PIPE).where(
                    PIPE.id == schema.pipe_id
                ))
                pipe = pipe_obj.scalar()

                if not pipe:
                    return json({'msg': 'Requested pipe not found'}, 404)

            except Exception as e:
                return json({'msg': 'Pipe fetch error', 'error': f'{str(e)}'}, 400)
            
            #Update Pipe
            pipe.name               = schema.pipe_name
            pipe.status             = schema.status
            pipe.is_active          = is_pipe_active
            pipe.connection_mode    = schema.connect_mode

            pipe.prod_url           = schema.prod_url
            pipe.test_url           = schema.test_url
            pipe.status_url         = schema.status_url
            pipe.refund_url         = schema.refund_url
            pipe.refund_policy      = schema.refund_pol
            pipe.whitelisting_ip    = schema.white_ip
            pipe.webhook_url        = schema.webhook_url
            pipe.whitelist_domain   = schema.white_domain
            
            pipe.auto_refund        = schema.auto_refnd
            
            pipe.headers            = schema.headers
            pipe.body               = schema.body
            pipe.query              = schema.query
            pipe.auth_keys          = schema.auth_keys

            pipe.redirect_msg       = schema.redirect_msg
            pipe.checkout_label     = schema.chkout_lable
            pipe.checkout_sub_label = schema.chkout_sub_lable
            pipe.comments           = schema.cmnt

            #Processing Mode
            pipe.process_mode      = schema.process_mod
            pipe.process_curr      = schema.process_cur
            pipe.settlement_period = schema.settlement_prd


            #Bank Response
            pipe.bank_max_fail_trans_allowed = schema.bnk_max_fail_trans_alwd
            pipe.bank_down_period            = schema.bnk_dwn_period
            pipe.bank_success_resp           = schema.bnk_sucs_resp
            pipe.bank_fail_resp              = schema.bnk_fl_resp
            pipe.bank_pending_res            = schema.bnk_pndng_res
            pipe.bank_status_path            = schema.bnk_stus_path

            #Bank Transaction
            pipe.bank_min_trans_limit = schema.bnk_min_trans_lmt
            pipe.bank_max_trans_limit = schema.bnk_max_trans_lmt
            pipe.bank_scrub_period    = schema.bnk_scrub_period
            pipe.bank_trxn_count      = schema.bnk_trxn_cnt
            pipe.bank_min_success_cnt = schema.bnk_min_sucs_cnt
            pipe.bank_min_fail_count  = schema.bnk_min_fl_count

            
            # Update Active countries into pipe
            if schema.active_cntry:
                active_country = ",".join(schema.active_cntry)
                exist_country  = pipe.process_country

                countries = exist_country.split(",") if exist_country else []

                if any(country == active_country for country in countries):
                    pass
                else:
                    pipe.process_country = active_country

            #Update Block countries in pipe
            if schema.block_cntry:
                block_country = ",".join(schema.block_cntry)
                exist_country = pipe.block_country

                countries = exist_country.split(",") if exist_country else []

                if any(country == block_country for country in countries):
                    pass
                else:
                    pipe.block_country = block_country

            # If pipe type IDs exists in request
            pipe_type_ids = schema.types

            if pipe_type_ids: 
                for type in pipe_type_ids:
                    check_pipe_type_obj = await session.execute(select(PIPEType).where(
                        PIPEType.id == type
                    ))
                    check_pipe_type = check_pipe_type_obj.scalar()

                    if check_pipe_type:
                        check_pipe_association_obj = await session.execute(select(PIPETypeAssociation).where(
                            and_(PIPETypeAssociation.pipe_id == pipe.id, PIPETypeAssociation.pipe_type_id == type)
                        ))
                        check_pipe_association_ = check_pipe_association_obj.scalar()

                        if not check_pipe_association_:
                            pipe_type_association = PIPETypeAssociation(
                                pipe_id = pipe.id, pipe_type_id = type
                            )

                            session.add(pipe_type_association)
                            await session.commit()
                            await session.refresh(pipe_type_association)

            session.add(pipe)
            await session.commit()
            await session.refresh(pipe)
            

            return json({'msg': 'Updated Successfully', 'data': pipe}, 200)
        
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    


#Delete Pipe by Admin
@auth('userauth')
@delete('/api/v5/admin/pipe/delete/')
async def Admin_pipe_delete(request: Request, query: int):
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id') if admin_identity else None

            if admin_id is None:
                return json({'msg': 'Unauthorized'}, 401)
            
            #Authenticate the user as Admin
            try:
                is_admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                is_admin_user = is_admin_user_obj.scalar()

                check_admin = is_admin_user.is_admin

                if not check_admin:
                    return json({'msg': 'Admin authorization failed'}, 403)

            except Exception as e:
                return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            #Admin Authentication ends

            #Get the pipe
            try:
                pipe_obj = await session.execute(select(PIPE).where(
                    PIPE.id == query
                ))
                pipe = pipe_obj.scalar()
                
                if not pipe:
                    return json({'msg': 'Requested pipe not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'Pipe fetch error', 'error': f'{str(e)}'}, 400)
            
            # Get all the pipetypeAssociation
            try:
                pipe_association_obj = await session.execute(select(PIPETypeAssociation).where(
                    PIPETypeAssociation.pipe_id == pipe.id
                ))
                pipe_associations_ = pipe_association_obj.scalars().all()
                
                # Delete pipe and its related types
                if pipe_associations_:
                    for pipe_association in pipe_associations_:
                        await session.delete(pipe_association)
                    await session.commit()
                    
            except Exception as e:
                return json({'msg': 'Pipe association fetch error', 'error': f'{str(e)}'}, 400)
            
            #Delete Pipe
            await session.delete(pipe)
            await session.commit()

            return json({'msg': 'Deleted Successfully'}, 200)
        
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)



#Get all pipe by Admin
@auth('userauth')
@get('/api/v5/admin/pipes/')
async def Admin_pipe(request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id') if admin_identity else None

            combined_data = []

            if admin_id is None:
                return json({'msg': 'Unauthorized'}, 401)
            
            #Authenticate the user as Admin
            try:
                is_admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                is_admin_user = is_admin_user_obj.scalar()

                check_admin = is_admin_user.is_admin

                if not check_admin:
                    return json({'msg': 'Admin authorization failed'}, 403)

            except Exception as e:
                return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            #Admin Authentication ends

            #Get all the available pipe
            try:
                pipe_obj = await session.execute(select(PIPE))
                all_pipe     = pipe_obj.scalars().all()
                
            except Exception as e:
                return json({'msg': 'Pipe fetch error', 'error': f'{str(e)}'}, 400)
            
            #Fetch currencies
            try:
                currency_obj = await session.execute(select(Currency))
                all_currency =  currency_obj.scalars().all()

            except Exception as e:
                return json({'msg': 'Currency fetch error'}, 400)
            
            #Fetch currencies
            try:
                pipe_type_obj = await session.execute(select(PIPEType))
                all_pipe_type     =  pipe_type_obj.scalars().all()

            except Exception as e:
                return json({'msg': 'Pipe type fetch error'}, 400)
            
            currency_dict  = {curr.id: curr for curr in all_currency}
            pipe_type_dict = {pipe_.id: pipe_ for pipe_ in all_pipe_type}
            
            for pipe in all_pipe:
                currency_id   = pipe.process_curr
                currency_data = currency_dict.get(currency_id)

                pipe_id = pipe.id
                # Fetch all pipe types
                try:
                    pipe_type_association_obj = await session.execute(select(PIPETypeAssociation).where(
                        PIPETypeAssociation.pipe_id == pipe_id
                    ))
                    pipe_type_association     =  pipe_type_association_obj.scalars().all()

                except Exception as e:
                    return json({'msg': 'Currency fetch error'}, 400)
                
                pipe_type_ids = [pipe_type_assoc.pipe_type_id for pipe_type_assoc in pipe_type_association]

                pipe_type_data = [pipe_type_dict.get(pipe_type_id) for pipe_type_id in pipe_type_ids]


                combined_data.append({
                    'id': pipe.id,
                    'body': pipe.body,
                    'status': pipe.status,
                    'refund_policy': pipe.refund_policy,
                    'process_curr': currency_data if currency_data else None,
                    'bank_min_trans_limit': pipe.bank_min_trans_limit,
                    'auto_refund': pipe.auto_refund,
                    'query': pipe.query,
                    'settlement_period': pipe.settlement_period,
                    'bank_max_trans_limit': pipe.bank_max_trans_limit,
                    'is_active': pipe.is_active,
                    'whitelisting_ip': pipe.whitelisting_ip,
                    'auth_keys': pipe.auth_keys,
                    'bank_max_fail_trans_allowed': pipe.bank_max_fail_trans_allowed,
                    'bank_scrub_period': pipe.bank_scrub_period,
                    'connection_mode': pipe.connection_mode,
                    'webhook_url': pipe.webhook_url,
                    'redirect_msg': pipe.redirect_msg,
                    'bank_down_period': pipe.bank_down_period,
                    'bank_trxn_count': pipe.bank_trxn_count,
                    'name': pipe.name,
                    'prod_url': pipe.prod_url,
                    'whitelist_domain': pipe.whitelist_domain,
                    'checkout_label': pipe.checkout_label,
                    'bank_success_resp': pipe.bank_success_resp,
                    'bank_min_success_cnt': pipe.bank_min_success_cnt,
                    'test_url': pipe.test_url,
                    'process_country': pipe.process_country,
                    'checkout_sub_label': pipe.checkout_sub_label,
                    'bank_fail_resp': pipe.bank_fail_resp,
                    'bank_min_fail_count': pipe.bank_min_fail_count,
                    'created_at': pipe.created_at,
                    'status_url': pipe.status_url,
                    'block_country': pipe.block_country,
                    'comments': pipe.comments,
                    'bank_pending_res': pipe.bank_pending_res,
                    'refund_url': pipe.refund_url,
                    'headers': pipe.headers,
                    'process_mode': pipe.process_mode,
                    'bank_status_path': pipe.bank_status_path,
                    'types': pipe_type_data if pipe_type_data else None,
                })



            return json({'msg': 'Pipe data fetched successfully', 'all_pipes_data': combined_data}, 200)
        
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)




#Get all pipe by Admin
@auth('userauth')
@get('/api/v5/admin/pipe/data/')
async def Admin_pipe(request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id') if admin_identity else None

            combined_data = []

            if admin_id is None:
                return json({'msg': 'Unauthorized'}, 401)
            
            #Authenticate the user as Admin
            try:
                is_admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                is_admin_user = is_admin_user_obj.scalar()

                check_admin = is_admin_user.is_admin

                if not check_admin:
                    return json({'msg': 'Admin authorization failed'}, 403)

            except Exception as e:
                return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            #Admin Authentication ends

            #Get all the available pipe
            try:
                pipe_obj = await session.execute(select(PIPE))
                all_pipe     = pipe_obj.scalars().all()
                
            except Exception as e:
                return json({'msg': 'Pipe fetch error', 'error': f'{str(e)}'}, 400)
            
            
            for pipe in all_pipe:

                combined_data.append({
                    'id': pipe.id,
                    'name': pipe.name,
                })

            return json({'msg': 'Pipe data fetched successfully', 'all_pipes_': combined_data}, 200)
        
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    


