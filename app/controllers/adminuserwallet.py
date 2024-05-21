# from blacksheep import Request, json, pretty_json
# from blacksheep.server.controllers import APIController
# from app.controllers.controllers import post
# from database.db import AsyncSession, async_engine
# from blacksheep.server.authorization import auth
# from sqlmodel import select
# from Models.models import Users, Wallet
# from Models.Admin.User.schemas import EachUserWalletSchema





# class AdminUserWalletView(APIController):

#     @classmethod
#     def route(cls) -> str | None:
#         return '/api/v2/admin/user/wallet/'
    
#     @classmethod
#     def class_name(cls) -> str:
#         return 'User wallet view by Admin'
    
    
#     @auth('userauth')
#     @post()
#     async def user_wallets(self, request: Request, schema: EachUserWalletSchema):
#         try:
#             async with AsyncSession(async_engine) as session:
#                 user_identity   = request.identity
#                 userID          = user_identity.claims.get("user_id") if user_identity else None

#                 #Check the user is admin or Not
#                 try:
#                     user_obj      = await session.execute(select(Users).where(Users.id == userID))
#                     user_obj_data = user_obj.scalar()

#                     if not user_obj_data.is_admin:
#                         return json({'msg': 'Only admin can view the Transactions'}, 400)
                    
#                 except Exception as e:
#                     return pretty_json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
                

#                 #Get the wallets related to the user
#                 try:
#                     user_wallet_obj = await session.execute(select(Wallet).where(Wallet.user_id == schema.user_id))
#                     user_wallets    = user_wallet_obj.scalars().all()

#                     if not user_wallets:
#                         return pretty_json({'msg': 'User Wallet not available'}, 404)

#                 except Exception as e:
#                     return pretty_json({'msg': 'Unable to get the Wallet of user', 'error': f'{str(e)}'}, 400)
                

#                 return pretty_json({'msg': 'Wallet fetched suuccessfully', 'user_wallet_data': user_wallets})
            

#         except Exception as e:
#             return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)