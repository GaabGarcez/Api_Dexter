from fastapi import FastAPI, Request, HTTPException, Depends
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class Message(BaseModel):
    messages: list

@app.get("/webhook")
async def verify_webhook(hub_mode: str, hub_challenge: str, hub_verify_token: str):
    VERIFY_TOKEN = "YOUR_VERIFY_TOKEN"  # Defina seu token de verificação aqui
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return {"hub.challenge": hub_challenge}
    else:
        raise HTTPException(status_code=403, detail="Verification token mismatch")

@app.post("/webhook")
async def receive_whatsapp_message(data: Message):
    for message in data.messages:
        sender_id = message.get("from")
        text = message.get("text", {}).get("body", "")
        print(f"Received message from {sender_id}: {text}")

    return {
        "messages": [
            {
                "to": sender_id,
                "content": {
                    "text": "Obrigado por enviar a mensagem. O Dexter está ficando brabo!"
                }
            }
        ]
    }


