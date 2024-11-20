from blacksheep import Application, WebSocket, ws, json, WebSocketDisconnectError



@ws('/ws')
async def ws_handler(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(msg)
            
    except WebSocketDisconnectError as e:
        return json({'message': f'Error - {str(e)}'}, 500)
