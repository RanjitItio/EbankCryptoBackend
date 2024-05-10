from blacksheep.server.controllers import post, APIController
from blacksheep import Request, json
from Models.schemas import GenerateToken
from app.auth import generate_access_token, generate_refresh_token
import time





class UserRefreshController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/token/'

    @classmethod
    def class_name(cls):
        return "Generate Token"

    @post()
    async def generate_token(self, request: Request, authToken: GenerateToken):
        try:
            req_boy = await request.json()
            get_id  = req_boy['user_id']

            if not get_id:
                return json({'msg': 'Please provide user id'}, 400)
            
            access_token = generate_access_token(get_id)
            refreh_token = generate_refresh_token(get_id)

            # if token['exp'] < time.time():
            #     return json({'msg': 'Refresh token expired'}, 400)
            
            return json({'access_token': access_token, 'refresh_token': refreh_token})

        except Exception as e:
            return json({'error': f'{str(e)}'}, 400)