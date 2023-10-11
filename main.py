from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import os
import httpx

app = FastAPI()

VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', "27032001")
WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN', "EABjyeHmZA4e4BOzjLT0U0AgVRSyTt7P1qcQMT2IoTGCFdqHQP4sNYLnPyf8NmXBCJNIvJ6VMeDTpEGejNaUO5iFsa3ZAOtSLx0EhUHHuPOh6zTke6mUNZAoPeYQ8MYHyx5Pu8OGRDMZB4lo5y6m2oy8nno6lPk688XmuYLCHMB5DO34Ow2v3lqcUMBa28IVW")

class WebhookPayload(BaseModel):
    object: str
    entry: list

@app.get("/webhook")
async def verify_webhook(hub_mode: str, hub_verify_token: str, hub_challenge: str):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return hub_challenge  # Respondendo com o valor de hub.challenge como uma string simples
    else:
        raise HTTPException(status_code=403, detail="Tokens do not match")

@app.post("/webhook")
async def handle_webhook(data: WebhookPayload):
    if data.object:
        entry = data.entry[0]
        if entry.get("changes"):
            change = entry["changes"][0]
            if change.get("value") and change["value"].get("messages"):
                phone_number_id = change["value"]["metadata"]["phone_number_id"]
                from_number = change["value"]["messages"][0]["from"]
                msg_body = change["value"]["messages"][0]["text"]["body"]
                
                url = f"https://graph.facebook.com/v12.0/{phone_number_id}/messages?access_token={WHATSAPP_TOKEN}"
                payload = {
                    "messaging_product": "whatsapp",
                    "to": from_number,
                    "text": {"body": "Ack: " + msg_body}
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload)
                    if response.status_code != 200:
                        raise HTTPException(status_code=response.status_code, detail=response.text)
                
                return {"status": "message sent"}
    raise HTTPException(status_code=400, detail="Not a valid request")
