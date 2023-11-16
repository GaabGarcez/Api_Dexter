from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio

app = FastAPI()

connections = {}
message_queues = {}
responses = {}

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def process_message(websocket: WebSocket, uuid: str):
    while True:  # Mantém o loop rodando continuamente
        if not message_queues[uuid].empty():
            message = await message_queues[uuid].get()
            await websocket.send_text(message)
            response = await websocket.receive_text()
            responses[uuid] = response  # Armazena a resposta
        else:
            await asyncio.sleep(0.1)  # Pequena pausa para evitar uso excessivo da CPU

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket
    if uuid not in message_queues:
        message_queues[uuid] = asyncio.Queue()
    await process_message(websocket, uuid)  # Processa mensagens continuamente

@app.post("/webhook/")
async def read_webhook(message: Message):
    target_uuid = message.uuid_user
    if target_uuid in connections:
        await message_queues[target_uuid].put(message.mensagem)
        while target_uuid not in responses:
            await asyncio.sleep(0.1)
        return {"response": responses.pop(target_uuid)}
    else:
        return {"response": "UUID não encontrado ou conexão não estabelecida"}
