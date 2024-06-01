from blacksheep import json, get



@get('/api/server/status/')
async def server_status(self):
    return json({'msg': 'Success'}, 200)



