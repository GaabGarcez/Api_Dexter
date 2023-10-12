from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import requests
import asyncio  # Adicionado importação de asyncio

app = FastAPI()

# Tabela de associação para mapear UUID para conexão WebSocket e mensagens pendentes
connections = {}
pending_messages = {}

class Message(BaseModel):
    numero: str
    mensagem: str

async def handle_websocket_messages(websocket: WebSocket, uuid: str):
    try:
        while True:
            if uuid in pending_messages:
                message = pending_messages.pop(uuid)
                await websocket.send_text(message)
            else:
                await asyncio.sleep(1)  # Adicione um pequeno atraso para evitar uso excessivo de CPU
    except:
        pass

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket
    await handle_websocket_messages(websocket, uuid)
    del connections[uuid]

@app.post("/webhook/")
async def read_webhook(message: Message):
    response = requests.post('https://xkit-1dzl-gome.n7c.xano.io/api:fbhumpeF/dexter_validacao', data={"numero": message.numero}, verify=False)

    data = response.json()

    if "Seu número não está cadastrado!" in data:
        return {"response": "Seu número não está cadastrado!"}
    
    uuid = data  # O Xano retorna o UUID diretamente

    # Verifique se temos uma conexão WebSocket para esse UUID
    if uuid in connections:
        pending_messages[uuid] = message.mensagem
        # Aguarde um pouco para dar tempo à coroutine handle_websocket_messages de processar a mensagem
        await asyncio.sleep(2)
        return {"response": "Mensagem enviada com sucesso!"}
    else:
        return {"response": "O dexter não está sendo executado no seu servidor."}
