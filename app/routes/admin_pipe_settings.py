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




# Create Pipe Connection mode by Admin
@auth('userauth')
@post('/api/v5/admin/pipe/connection/mode/new/')
async def AdminPipeConnectionModeCreate(request: Request, schema: AdminPipeConnectionModeCreateSchema):
    """
        Creates a new Pipe Connection Mode by an Admin.<br/>
        <br/>
        Parameters:<br/>
            - request (Request): The incoming request.<br/>
            - schema (AdminPipeConnectionModeCreateSchema): The schema containing the name of the Pipe Connection Mode.<br/><br/>
        
        Returns:<br/>
            - JSON: A JSON response containing the success message and the created Pipe Connection Mode.<br/>
            - JSON: A JSON response containing an error message and the HTTP status code.<br/><br/>

        Error message:<br/>
            - JSON: A JSON response containing an error message and the HTTP status code.<br/>
            - Error 401: 'Unauthorized'<br/>
            - Error 403: 'Admin authorization failed'<br/>
            - Error 400: 'Admin authentication error'<br/>
            - Error 500: 'Server Error'<br/><br/>

        Raises:<br/>
            - HTTPException: If the request payload is invalid or if the user is not authenticated or if the admin authorization fails.<br/>
            - HTTPStatus: 401 Unauthorized if the user is not authenticated or if the admin authorization fails.<br/>
            - HTTPStatus: 403 Admin authorization failed if the user is not an admin.<br/>
            - HTTPStatus: 400 Admin authentication error if the user is not authenticated.<br/>
            - HTTPStatus: 500 Internal Server Error if an error occurs.<br/>
    """
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





# Update Pipe Connection mode by Admin
@auth('userauth')
@put('/api/v5/admin/pipe/connection/mode/update/')
async def AdminPipeConnectionModeUpdate(request: Request, schema: AdminPipeConnectionModeUpdateSchema):
    """
        This API Endpoint let admin update a pipe connection mode.<br/>
        Admin needs to be authenticated and have admin rights to perform this operation.<br/><br/>

        Parameters:<br/>
            - request (Request): The HTTP Request object containing the user's identity and payload data.<br/>
            - schema (AdminPipeConnectionModeUpdateSchema): The schema object containing the connection_id and mode.<br/><br/>
        
        Returns:<br/>
            - JSON: A JSON response containing the success status, message, or error details.<br/><br/>

        Raises:<br/>
            - Unauthorized: If the user is not authenticated or not admin.<br/>
            - Forbidden: If the user is authenticated but not admin.<br/>
            - NotFound: If the requested connection not found.<br/>
            - BadRequest: If the payload data is invalid.<br/>
            - ServerError: If any other error occurs during the API operation.<br/><br/>

        Error Messages:<br/>
            - 'msg': 'Admin authorization failed'<br/>
            - 'msg': 'Admin authentication error'<br/>
            - 'msg': 'Requested connection not found'<br/>
            - 'msg': 'Pipe fetch error'<br/>
            - 'msg': 'Server error'<br/>
    """
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
    




# Delete Pipe Connection mode by Admin
@auth('userauth')
@delete('/api/v5/admin/pipe/connection/mode/delete/')
async def AdminPipeConnectionModeDelete(request: Request, query: int):
    """
        This API Endpoint let admin delete a pipe connection mode.<br/>
        Admin needs to be authenticated and have admin rights to perform this operation.<br/><br/>

        Parameters:<br/>
            - request (Request): The HTTP Request object containing the user's identity and payload data.<br/>
            - query (int): The ID of the pipe connection mode to be deleted.<br/><br/>
            
        Returns:<br/>
            - JSON: A JSON response containing the success status, message, or error details.<br/><br/>
        
        Raises:<br/>
            - Unauthorized: If the user is not authenticated or not admin.<br/>
            - Forbidden: If the user is authenticated but not admin.<br/>
            - NotFound: If the requested pipe connection mode not found.<br/>
            - ServerError: If any other error occurs during the database operations.<br/><br/>

        Error Messages:<br/>
            - Unauthorized: If the user is not authenticated as admin.<br/>
            - Forbidden: If the user is authenticated but not admin.<br/>
            - NotFound: If the requested pipe connection mode not found.<br/>
            - ServerError: If any other error occurs during the database operations.<br/>
    """
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
    """
        Get all the pipes conncetion modes.<br/><br/>

        Parameters:<br/>
          request: Request object<br/><br/>

        Returns:<br/>
          JSON: A JSON response containing all the pipe connection modes.<br/>
          If unauthorized, returns 401 status code.<br/>
          If server error, returns 500 status code.<br/><br/>

        Raises:<br/>
          ValueError: If the request data is invalid.<br/>
    """
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
    """
        This API Endpoint let admin create a country.<br/><br/>

        Parameters:<br/>
            - request (Request): Request object<br/>
            - schema (AdminCountryCreateSchema): Schema object containing the country details<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the following keys:<br/>
                - msg (str): Success message<br/>
                - data (Country): Created country object<br/><br/>

        Error message:<br/>
            - Unauthorized: If user is not authenticated as an admin<br/>
            - Admin authorization failed: If user is authenticated but not an admin<br/>
            - Admin authentication error: If admin authentication fails<br/>
            - Server Error: If an error occurs during the database operations<br/><br/>

        Raises:<br/>
            - HTTPException: If the request payload is invalid or if the user is not authenticated as admin<br/>
            - HTTPStatus: 400 Bad Request if the request payload is invalid<br/>
            - HTTPStatus: 401 Unauthorized if user is not authenticated as an admin<br/>
            - HTTPStatus: 403 Admin authorization failed if user is authenticated but not an admin<br/>
            - HTTPStatus: 400 Admin authentication error if admin authentication fails<br/>
            - HTTPStatus: 500 Internal Server Error if an error occurs during the database operations<br/>
    """
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
    """
        This API Endpoint let Admin to update a country.<br/><br/>

        Parameters:<br/>
            country_id (int): ID of the country to be updated.<br/>
            name (str): New name of the country.<br/>
            request (Request): HTTP request object.<br/>
            schema(AdminCountryUpdateSchema): Admin country update schema object.<br/><br/>

        Returns:<br/>
            - dict: JSON response containing success status, message or error details.<br/><br/>

        Raises:<br/>
            - HTTPError: If the request fails due to an error.<br/><br/>

        Error Messages:<br/>
            - Unauthorized: If the user is not authorized to perform this operation.<br/>
            - 'msg': 'Requested country not found'<br/>
            - 'msg': 'Country fetch error'<br/>
            - 'msg': 'Admin authorization failed'<br/>
    """
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
    """
        Delete country by Admin.<br/><br/>

        Parameters:<br/>
            query (int): ID of the country to delete.<br/>
            request (Request): HTTP request object.<br/><br/>

        Returns:<br/>
            - dict: JSON response containing success status 200, message or error details.<br/>
            - If the country is not found, returns a 404 status code.<br/>
            - If an error occurs, returns a 500 status code.<br/>
            - If the admin is not authorized, returns a 403 status code.<br/><br/>
        
        Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
            - SQLAlchemy exception if there is any error during the database query or response generation.<br/><br/>

        Error message:<br/>
            - Unauthorized: If the user is not authorized to access the endpoint.<br/>
            - Server Error: If an error occurs while executing the database query.<br/>
            - Requested country not found: If the requested country is not found.<br/>
            - Country fetch error: If an error occurs while fetching the country information.<br/>
    """
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
async def AdminAllCountries(request: Request):
    """
        Get all available countries.<br/>
        This endpoint is only accessible by admin users.<br/><br/>
        
        Parameters:<br/>
        - request (Request): The HTTP request object.<br/><br/>
        
        Returns:<br/>
        - JSON: A JSON response containing all available countries.<br/>
        - HTTP Status Code: 200 in case of successful operation.<br/>
        - HTTP Status Code: 401 in case of unauthorized access.<br/>
        - HTTP Status Code: 500 in case of server errors.<br/><br/>
        
        Raises:<br/>
        - Exception: If any error occurs during the database operations.<br/><br/>

        Error Messages:<br/>
        - Unauthorized: If the user is not authenticated as admin.<br/>
        - Admin authorization failed: If the user is not authorized to access the endpoint.<br/>
        - Server Error: If an error occurs during the database operations.<br/>
    """
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
    """
        Create a new pipe type(Debit Card, Credit Card, Amex etc.) by admin.<br/><br/>

        Parameters:<br/>
         - request (Request): HTTP request object.<br/>
         - schema (AdminPipeTypeCreateSchema): Schema containing pipe type details.<br/><br/>

        Returns:<br/>
         - JSON: A JSON response containing the success status, message, or error details.<br/>
         - HTTP status code: 201 - Created if successful, 400 - Bad Request if validation fails, 401 - Unauthorized if not admin, 403 - Forbidden if admin authorization fails.<br/>
         - HTTP status: 500 - Internal Server Error if an error occurs during database operations.<br/><br/>

        Raises:<br/>
         - Exception: If any unexpected error occurs during database operations.<br/><br/>

        Error Messages:<br/>
         - Unauthorized: If the user is not authenticated as admin.<br/>
         - Server Error: If an error occurs during database operations.<br/>
         - Forbidden: If admin authorization fails.<br/>
    """
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
    





# Update Pipe Type by Admin
@auth('userauth')
@put('/api/v5/admin/pipe/type/update/')
async def AdminPipeTypeUpdate(request: Request, schema: AdminPipeTypeUpdateSchema):
    """
        This API Endpoint let admin update the pipe types.<br/><br/>

        Parameters:<br/>
            - schema(AdminPipeTypeUpdateSchema): The schema to update the pipe types.<br/>
            - request(Request): The request object containing the admin's identity.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response indicating the success or failure of the operation.<br/>
            - On success, returns a 200 status code with a message indicating that the pipe type has been updated.<br/>
            - On failure, returns appropriate error status codes with error messages.<br/><br/>
        
        Error message:<br/>
            - 'msg': 'Admin authorization failed'<br/>
            - 'msg': 'Admin authentication error'<br/>
            - 'msg': 'Requested pipe type not found'<br/>
            - 'msg': 'Pipe fetch error'<br/>
            - 'msg': 'Server error'<br/><br/>

        Raises:<br/>
            - Exception: If any error occurs during the operation, JSON response with an appropriate error message is returned.<br/>
            - ValueError: If the input data is not valid.<br/>
            - Error 401: 'Unauthorized' if admin is not authenticated.<br/>
            - Error 403: 'Forbidden' if admin does not have sufficient privileges to update the pipe type.<br/>
            - Error 500: 'Server error'<br/>
            - Error 404: 'Requested pipe type not found'<br/>
    """
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
    





# Delete Pipe Type by Admin
@auth('userauth')
@delete('/api/v5/admin/pipe/type/delete/')
async def AdminPipeTypeDelete(request: Request, query: int):
    """
        Deletes a Pipe Type by an Admin.<br/>
        <br/>
        Parameters:<br/>
            - request (Request): The incoming request.<br/>
            - query (int): The ID of the Pipe Type to delete.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response with a success message and status 200.<br/>
            - JSON: A JSON response with an error message and HTTP status code 400.<br/>
            - Error 401: 'Unauthorized'<br/>
            - Error 403: 'Admin authorization failed'<br/><br/>

        Raises:<br/>
            - HTTPException: If the user is not authenticated as an admin or if the admin authorization fails.<br/><br/>
        
        Error message:<br/>
            - 'Unauthorized': User is not authenticated as an admin.<br/>
            - 'Admin authorization failed': User is not an admin.<br/>
            - 'Requested pipe type not found': Pipe Type not found in the database.<br/>
            - 'Pipe fetch error': Error occurred while deleting the Pipe Type from the database.<br/>
            - 'Server error': An unexpected error occurred while deleting the Pipe Type.<br/>
    """
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
async def AdminPIPEType(request: Request):
    """
        Get all available Pipe Type by Admin.<br/><br/>
        
        Parameters:<br/>
           - request: Request object.<br/><br/>

        Returns:<br/>
            - JSON: JSON object containing the Pipe Types.<br/>
            - 400: Bad Request if there's an error fetching Pipe Types.<br/>
            - 500: Server Error if there's an error in the server.<br/>
            - 401: Unauthorized if the user is not authenticated.<br/><br/>

        Raises:<br/>
            - HTTPException: If the user is not authenticated.<br/>
            - HTTPStatus: 400 Bad Request if there's an error fetching Pipe Types.<br/>
            - HTTPStatus: 500 Server Error if there's an error in the server.<br/><br/>

        Error Messages:<br/>
            - 401: Unauthorized<br/>
            - 500: Internal Server Error<br/>
            - 400: Bad Request<br/>
    """
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