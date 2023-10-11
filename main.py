from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import os
import httpx

app = FastAPI()

os.environ['VERIFY_TOKEN'] = "27032001"
os.environ['WHATSAPP_TOKEN'] = "EABjyeHmZA4e4BOzjLT0U0AgVRSyTt7P1qcQMT2IoTGCFdqHQP4sNYLnPyf8NmXBCJNIvJ6VMeDTpEGejNaUO5iFsa3ZAOtSLx0EhUHHuPOh6zTke6mUNZAoPeYQ8MYHyx5Pu8OGRDMZB4lo5y6m2oy8nno6lPk688XmuYLCHMB5DO34Ow2v3lqcUMBa28IVW"

class WebhookPayload(BaseModel):
    object: str
    entry: list

@app.get("/webhook")
async def verify_webhook(hub_mode: str, hub_verify_token: str, hub_challenge: str):
    if hub_mode == "subscribe" and hub_verify_token == os.environ['VERIFY_TOKEN']:
        return {"hub.challenge": hub_challenge}
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
                
                url = f"https://graph.facebook.com/v12.0/{phone_number_id}/messages?access_token={os.environ['WHATSAPP_TOKEN']}"
                payload = {
                    "messaging_product": "whatsapp",
                    "to": from_number,
                    "text": {"body": "Ack: " + msg_body}
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload)
                
                return {"status": "message sent"}
    return {"status": "not a valid request"}
