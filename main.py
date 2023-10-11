# whatsapp_server.py

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Message(BaseModel):
    messages: list

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
                    "text": "O Dexter está ficando brabo!"
                }
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
