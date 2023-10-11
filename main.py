from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

app = FastAPI()

VERIFY_TOKEN = "EABjyeHmZA4e4BOzjLT0U0AgVRSyTt7P1qcQMT2IoTGCFdqHQP4sNYLnPyf8NmXBCJNIvJ6VMeDTpEGejNaUO5iFsa3ZAOtSLx0EhUHHuPOh6zTke6mUNZAoPeYQ8MYHyx5Pu8OGRDMZB4lo5y6m2oy8nno6lPk688XmuYLCHMB5DO34Ow2v3lqcUMBa28IVW"  # Substitua pelo seu token de verificação

class WhatsAppMessage(BaseModel):
    from_: str
    text: dict

@app.get("/webhook")
async def verify_webhook(hub_mode: str, hub_challenge: str, hub_verify_token: str):
    if hub_verify_token == VERIFY_TOKEN:
        return {"hub.challenge": hub_challenge}
    else:
        raise HTTPException(status_code=403, detail="Token de verificação incorreto")

@app.post("/webhook")
async def receive_whatsapp_message(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    for message in messages:
        sender_id = message.get("from")
        text = message.get("text", {}).get("body", "")
        print(f"Received message from {sender_id}: {text}")

    # Aqui, você pode adicionar a lógica para enviar uma resposta usando a API do WhatsApp Business.
    # Por simplicidade, estou apenas retornando a mensagem de resposta, mas na prática, você faria uma chamada API para enviar a mensagem.
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

