import httpx




# Send Master card Webhook Response to Client
class WebhookPayload:
    def __init__(self, success: bool, status: str, message: str, data: dict) -> None:
        self.success = success
        self.status  = status
        self.message = message
        self.data    = data



async def send_pg_webhook(url: str, payload: WebhookPayload):
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={
            "success": payload.success,
            "status":  payload.status,
            "message": payload.message,
            "data":    payload.data
        })

        return response


# @post('/api/send-webhook/')
async def send_webhook_response(payload: WebhookPayload, url: str):

    try:
        response = await send_pg_webhook(url, payload)

        if response.status_code == 200:
            return {"message": "Webhook sent successfully"}
        else:
            return {"message": "Failed to send webhook", "status_code": response.status_code}
        
    except Exception as e:
        return {"message": "An error occurred while sending the webhook", "error": str(e)}