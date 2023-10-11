# whatsapp_server.py

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI()

VERIFY_TOKEN = "SeuTokenDeVerificação"  # Substitua por seu token de verificação real

class Message(BaseModel):
    messages: list

@app.get("/webhook")
async def verify_webhook(hub_mode: str, hub_challenge: str, hub_verify_token: str):
    if hub_verify_token == VERIFY_TOKEN:
        return {"hub.challenge": int(hub_challenge)}
    else:
        raise HTTPException(status_code=403, detail="Token de verificação incorreto")

@app.post("/webhook")
async def receive_whatsapp_message(data: Message):
    # Processar as mensagens recebidas
    for message in data.messages:
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
