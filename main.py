from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
import uuid

app = FastAPI()

connections = {}
message_queues = {}
responses = {}

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def process_message(websocket: WebSocket, uuid: str):
    while True:
        if not message_queues[uuid].empty():
            message_id, message = await message_queues[uuid].get()
            await websocket.send_text(f"{message_id}:{message}")  # Envio de message_id com a mensagem
            response = await websocket.receive_text()
            responses[message_id] = response  # Associa a resposta ao identificador da mensagem
        else:
            await asyncio.sleep(0.1)

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket
    if uuid not in message_queues:
        message_queues[uuid] = asyncio.Queue()
    await process_message(websocket, uuid)

@app.post("/webhook/")
async def read_webhook(message: Message):
    target_uuid = message.uuid_user
    message_id = str(uuid.uuid4())  # Identificador único para a mensagem
    if target_uuid in connections:
        await message_queues[target_uuid].put((message_id, message.mensagem))
        while message_id not in responses:
            await asyncio.sleep(0.1)
        return {"response": responses.pop(message_id)}  # Retorna a resposta associada ao identificador
    else:
        return {"response": "UUID não encontrado ou conexão não estabelecida"}
