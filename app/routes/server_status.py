from blacksheep import json, get, post, Request, FromForm, FromFiles
from blacksheep.exceptions import BadRequest, HTTPException
from pathlib import Path
from blacksheep.cookies import Cookie, CookieSameSiteMode
from app.auth import generate_access_token, generate_refresh_token





@get('/api/server/status/')
async def server_status(self):
    return json({'msg': 'Success'}, 200)


@get('/api/set-cookie/')
async def Set_Cookie(request: Request):
    user_identity = request.identity
    user_id       = user_identity.claims.get('user_id') if user_identity else None


    if not user_identity:
        return json({'error': 'Unauthorized'}, 401)
    
    response = json({'msg': 'Success'}, 200)

    response.set_cookies([
        Cookie(
            'access_token', generate_access_token(user_id),
            http_only=False,
            same_site=CookieSameSiteMode.NONE,
            secure=True,
            path='/',
            domain='localhost'
        ),
        Cookie(
            'refresh_token',  generate_refresh_token(user_id),
            http_only=False,
            same_site=CookieSameSiteMode.NONE,
            secure=True,
            path='/',
            domain='localhost'
            )
    ])

    return response


@post('/api/upload-file/')
async def file_upload(self, request: Request):
    files = await request.files()

    for part in files:
        file_bytes = part.data
        file_name  = part.file_name.decode()

    file_path = Path("Static") / file_name

    try:
        with open(file_path, mode="wb") as example_file:
            example_file.write(file_bytes)

    except Exception:
        file_path.unlink()
        raise
    
    return json({'msg': 'Success'})



# @post('/api/upload-file/second/')
# async def file_uploade_second(self, request: Request):
#     files = await request.files()

#     for part in files:
#         file = part.file_name
    
#     file_name = file.decode()
#     file_path = Path("Static") / file_name

#     if not file_name:
#         raise BadRequest("Missing file name.")

#     try:
#         with open(file_path, mode="wb") as example_file:
#             async for chunk in read_stream(request):
#                 example_file.write(chunk)

#     except MaxBodyExceededError:
#         file_path.unlink()
#         raise

#     return {"status": "OK", "uploaded_file": file_name}


# class MaxBodyExceededError():
#     def __init__(self, max_size: int):
#         super().__init__(413, "The request body exceeds the maximum size.")
#         self.max_size = max_size


# async def read_stream(request: Request, max_body_size: int = 1500000):
#     """
#     Reads a request stream, up to a maximum body length (default to 1.5 MB).
#     """
#     current_length = 0
#     async for chunk in request.stream():
#         current_length += len(chunk)
#         print(current_length)
#         if max_body_size > -1 and current_length > max_body_size:
#             raise MaxBodyExceededError(max_body_size)

#         yield chunk
