from blacksheep.server.controllers import APIController
from blacksheep import Request, json
from Models.schemas import GenerateToken
from app.auth import generate_access_token, generate_refresh_token
from app.auth import decode_token
from app.controllers.controllers import get, post, put, delete





class UserRefreshController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/token/'

    @classmethod
    def class_name(cls):
        return "Generate Token"

    @post()
    async def generate_token(self, request: Request):
        try:
            req_body = await request.json()
            refresh_token = req_body['refresh_token']

            try:
                user_data = decode_token(refresh_token)
            except Exception as e:
                return json({'mag': 'Decoding error', 'error': f'{str(e)}'})

            if user_data == 'Token has expired':
                return json({'msg': 'Token has expired'}, 400)
            elif user_data == 'Invalid token':
                return json({'msg': 'Invalid token'}, 400)
            else:
                user_data = user_data
                
            userID = user_data["user_id"]

            if not userID:
                return json({'msg': 'Please provide user id'}, 400)
            
            access_token = generate_access_token(userID)
            refreh_token = generate_refresh_token(userID)

            # # if token['exp'] < time.time():
            # #     return json({'msg': 'Refresh token expired'}, 400)
            
            return json({'access_token': access_token, 'refresh_token': refreh_token})

        except Exception as e:
            return json({'msg': 'Server Error','error': f'{str(e)}'}, 500)