from blacksheep.server.authorization import auth
from blacksheep import get, post, put, delete, Request, json
from database.db import AsyncSession, async_engine
from sqlmodel import select
from Models.models import Users
from Models.models2 import PIPEConnectionMode, PIPEType, Country
from Models.Admin.PIPE.pipeschema import (
    AdminPipeConnectionModeCreateSchema, AdminPipeConnectionModeUpdateSchema,
    AdminCountryCreateSchema, AdminCountryUpdateSchema, AdminPipeTypeCreateSchema,
    AdminPipeTypeUpdateSchema
    )



#Create Pipe Connection mode by Admin
@auth('userauth')
@post('/api/v5/admin/pipe/connection/mode/new/')
async def AdminPipeConnectionModeCreate(request: Request, schema: AdminPipeConnectionModeCreateSchema):
    try: 
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id') if admin_identity else None

            pipe_name = schema.name

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

            #Create Pipe connection
            pipe_connection = PIPEConnectionMode(
                name = pipe_name
            )

            session.add(pipe_connection)
            await session.commit()
            await session.refresh(pipe_connection)

            return json({'msg': 'Created successfully', 'data': pipe_connection}, 201)
    
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)



#Update Pipe Connection mode by Admin
@auth('userauth')
@put('/api/v5/admin/pipe/connection/mode/update/')
async def AdminPipeConnectionModeUpdate(request: Request, schema: AdminPipeConnectionModeUpdateSchema):
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

            #Get the Pipe connection
            try:
                pipe_connection_obj = await session.execute(select(PIPEConnectionMode).where(
                    PIPEConnectionMode.id == schema.connection_id
                ))
                pipe_connection = pipe_connection_obj.scalar()

                if not pipe_connection:
                    return json({'msg': 'Requested connection not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'Pipe fetch error', 'error': f'{str(e)}'}, 400)
            
            #Update Pipe
            pipe_connection.name = schema.name

            session.add(pipe_connection)
            await session.commit()
            await session.refresh(pipe_connection)

            return json({'msg': 'Updated successfully', 'data': pipe_connection}, 200)
    
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    


#Delete Pipe Connection mode by Admin
@auth('userauth')
@delete('/api/v5/admin/pipe/connection/mode/delete/')
async def AdminPipeConnectionModeDelete(request: Request, query: int):
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

            #Get the Pipe connection
            try:
                pipe_connection_obj = await session.execute(select(PIPEConnectionMode).where(
                    PIPEConnectionMode.id == query
                ))
                pipe_connection     = pipe_connection_obj.scalar()

                if not pipe_connection:
                    return json({'msg': 'Requested connection not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'Pipe fetch error', 'error': f'{str(e)}'}, 400)
            
            #Delete Pipe
            await session.delete(pipe_connection)
            await session.commit()

            return json({'msg': 'Deleted successfully'}, 200)
    
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)




#Get all Pipe Connection mode by Admin
@auth('userauth')
@get('/api/v5/admin/pipe/connection/modes/')
async def AdminPipeConnectionModes(request: Request):
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

            #Get the Pipe connection
            try:
                pipe_connection_obj = await session.execute(select(PIPEConnectionMode))
                pipe_connection     = pipe_connection_obj.scalars().all()

                if not pipe_connection:
                    return json({'msg': 'Requested connection not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'Pipe fetch error', 'error': f'{str(e)}'}, 400)
            

            return json({'msg': 'Pipe connection mode data fetched successfully', 'all_pipe_connections': pipe_connection}, 200)
    
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    



#Create Country mode by Admin
@auth('userauth')
@post('/api/v5/admin/country/new/')
async def AdminCountryCreate(request: Request, schema: AdminCountryCreateSchema):
    try: 
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id') if admin_identity else None

            pipe_country_name = schema.name

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

            #Create Pipe connection
            country = Country(
                name = pipe_country_name
            )

            session.add(country)
            await session.commit()
            await session.refresh(country)

            return json({'msg': 'Created successfully', 'data': country}, 201)
    
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
   



#Update Country by Admin
@auth('userauth')
@put('/api/v5/admin/country/update/')
async def AdminCountryUpdate(request: Request, schema: AdminCountryUpdateSchema):
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

            #Get the Country
            try:
                pipe_country_obj = await session.execute(select(Country).where(
                    Country.id == schema.country_id
                ))
                pipe_country = pipe_country_obj.scalar()

                if not pipe_country:
                    return json({'msg': 'Requested country not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'Country fetch error', 'error': f'{str(e)}'}, 400)
            
            #Update Pipe
            pipe_country.name = schema.name

            session.add(pipe_country)
            await session.commit()
            await session.refresh(pipe_country)

            return json({'msg': 'Updated successfully', 'data': pipe_country}, 200)
    
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    



#Delete Country by Admin
@auth('userauth')
@delete('/api/v5/admin/country/delete/')
async def AdminCountryDelete(request: Request, query: int):
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


            #Get the Pipe connection
            try:
                pipe_country_obj = await session.execute(select(Country).where(
                    Country.id == query
                ))
                pipe_country     = pipe_country_obj.scalar()

                if not pipe_country:
                    return json({'msg': 'Requested country not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'Country fetch error', 'error': f'{str(e)}'}, 400)
            
            #Delete Country
            await session.delete(pipe_country)
            await session.commit()

            return json({'msg': 'Deleted successfully'}, 200)
    
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    



#Get all available Country by Admin
@auth('userauth')
@get('/api/v5/admin/countries/')
async def AdminCountryDelete(request: Request):
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


            #Get the Pipe connection
            try:
                pipe_country_obj = await session.execute(select(Country))
                pipe_country     = pipe_country_obj.scalar()
                
            except Exception as e:
                return json({'msg': 'Country fetch error', 'error': f'{str(e)}'}, 400)

            return json({'msg': 'Country data fetched successfully', 'all_countries': pipe_country}, 200)
    
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    



#Create Pipe type by Admin
@auth('userauth')
@post('/api/v5/admin/pipe/type/create/')
async def AdminPipeTypeCreate(request: Request, schema: AdminPipeTypeCreateSchema):
    try: 
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id') if admin_identity else None

            pipe_type_name = schema.name

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

            #Create Pipe connection
            pipe_type = PIPEType(
                name = pipe_type_name
            )

            session.add(pipe_type)
            await session.commit()
            await session.refresh(pipe_type)

            return json({'msg': 'Created successfully', 'data': pipe_type}, 201)
    
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    



#Update Pipe Type by Admin
@auth('userauth')
@put('/api/v5/admin/pipe/type/update/')
async def AdminCountryUpdate(request: Request, schema: AdminPipeTypeUpdateSchema):
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

            #Get the Country
            try:
                pipe_type_obj = await session.execute(select(PIPEType).where(
                    PIPEType.id == schema.pipe_type_id
                ))
                pipe_type = pipe_type_obj.scalar()

                if not pipe_type:
                    return json({'msg': 'Requested pipe type not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'Pipe fetch error', 'error': f'{str(e)}'}, 400)
            
            #Update Pipe
            pipe_type.name = schema.name

            session.add(pipe_type)
            await session.commit()
            await session.refresh(pipe_type)

            return json({'msg': 'Updated successfully', 'data': pipe_type}, 200)
    
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    


#Delete Pipe Type by Admin
@auth('userauth')
@delete('/api/v5/admin/pipe/type/delete/')
async def AdminCountryUpdate(request: Request, query: int):
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

            #Get the Country
            try:
                pipe_type_obj = await session.execute(select(PIPEType).where(
                    PIPEType.id == query
                ))
                pipe_type = pipe_type_obj.scalar()

                if not pipe_type:
                    return json({'msg': 'Requested pipe type not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'Pipe fetch error', 'error': f'{str(e)}'}, 400)
          
            #Delete Pipe Type
            await session.delete(pipe_type)
            await session.commit()

            return json({'msg': 'Deleted successfully'}, 200)
    
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)





#Get all available Pipe Type by Admin
@get('/api/v5/admin/pipe/types/')
async def AdminCountryUpdate(request: Request):
    try: 
        async with AsyncSession(async_engine) as session:

            #Get all the Pipe Types
            try:
                pipe_type_obj = await session.execute(select(PIPEType))
                pipe_type     = pipe_type_obj.scalars().all()
                
            except Exception as e:
                return json({'msg': 'Pipe fetch error', 'error': f'{str(e)}'}, 400)
            

            return json({'msg': 'Data fetched successfully', 'all_pipe_type': pipe_type}, 200)
    
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)