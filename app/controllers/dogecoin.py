from blacksheep.server.controllers import get, post, put, delete, APIController
from Models.schemas import UserCreateSchema ,UserLoginSchema
from sqlmodel import Session, select
from database.db import engine
from Models.models import Users
from blacksheep import Request
from blacksheep import  json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token ,generate_refresh_token
from Models.cryptoapi import Dogecoin
from ..settings import CRYPTO_CONFIG ,SECURITIES_CODE




dogecoin=Dogecoin(CRYPTO_CONFIG["dogecoin_api_key"],SECURITIES_CODE)
class DogecoinBalanceController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/Dogecoin/GetBalance'
    
    @classmethod
    def class_name(cls):
        return "Users login"
    
    
    @get()
    def get_dogecoin_balance(self,request: Request):
        address = request.query_params.get("address")
      
        dogecoin_balance=dogecoin.get_balance(address)
        if dogecoin_balance:
            return json({'balance':dogecoin_balance})
        else:
            return json({'msg': 'Error getting dogecoin balance'}, 400)
        
        
class DogecoinTransectionController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/Dogecoin/GetTransection'
    
    @classmethod
    def class_name(cls):
        return "Users login"
    
    
    @get()
    def get_dogecoin_balance(self,request: Request):
        address = request.query_params.get("address")
        type = request.query_params.get("type")
        dogecoin_balance=dogecoin.get_transection(address,type)
        if dogecoin_balance:
            return json({'balance':dogecoin_balance})
        else:
            return json({'msg': 'Error getting dogecoin balance'}, 400)
    
    
class DogecoinSendController(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/Dogecoin/Send'

    @classmethod
    def class_name(cls):
        return "Dogecoin Send Controller"
    
    @post()
    def send_dogecoin(self, request: Request):
        data = request.query_params
        sender_address =  data.get("sender_address")
        receiver_address = data.get("receiver_address")
        priority = data.get("priority")
        amount = data.get("amount")
        try:
            tx_hash = dogecoin.prepare_transaction(amounts=amount,from_addresses=sender_address,to_addresses=receiver_address ,priority=priority)
            if tx_hash:
                return json({"tx_hash": tx_hash})
            else:
                return json({"msg": "Error sending Dogecoin"}, 400)
        except Exception as e:
            return json({"msg": str(e)}, 400)
    
    
        
    


