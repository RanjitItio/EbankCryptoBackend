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




dogecoin=Dogecoin(CRYPTO_CONFIG["bitcoin_api_key"],SECURITIES_CODE)
class BitcoinBalanceController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/Bitcoin/GetBalance'
    
    @classmethod
    def class_name(cls):
        return "BITCOIN BALANCE CONTROLLER"
    
    
    @get()
    def get_dogecoin_balance(self,request: Request):
        address = request.query_params.get("address")
      
        dogecoin_balance=dogecoin.get_balance(address)
        if dogecoin_balance:
            return json({'balance':dogecoin_balance})
        else:
            return json({'msg': 'Error getting dogecoin balance'}, 400)
        
        
class BitcoinTransectionController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/Bitcoin/GetTransection'
    
    @classmethod
    def class_name(cls):
        return "Bitcoin Transection Controller"
    
    
    @get()
    def get_dogecoin_balance(self,request: Request):
        address = request.query_params.get("address")
        type = request.query_params.get("type")
        dogecoin_balance=dogecoin.get_transection(address,type)
        if dogecoin_balance:
            return json({'balance':dogecoin_balance})
        else:
            return json({'msg': 'Error getting dogecoin balance'}, 400)
    
    
    
        
    


