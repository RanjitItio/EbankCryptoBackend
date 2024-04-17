# """
# Example API implemented using a controller.
# """
# from typing import List, Optional
# from blacksheep import json

# from blacksheep.server.controllers import get, post, put, delete, APIController


# class Example:
#     examples = str


# class ExampleUserController(APIController):
#     @classmethod
#     def route(cls) -> Optional[str]:
#         return "/api/examples"
    
#     @classmethod
#     def class_name(cls) -> str:
#         return "Examples"
    
#     @get()
#     async def get_example(self) -> List[str]:
#         """
#         Gets a list of examples.
#         """
#         return list(f"example {i}" for i in range(3))

#     @post()
#     async def add_example(self, example: str):
#         return json({'example': example})
    
#     @put()
#     async def update_example(self, example: str):
#         return json({'example': example})
    
#     @delete()
#     async def delete_example(self, example: str):
#         return json({'example': example})
    

