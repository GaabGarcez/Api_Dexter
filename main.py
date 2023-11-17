from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
import uuid

app = FastAPI()

connections = {}
message_queues = {}
responses = {}
response_events = {}

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def process_message(uuid: str):
    while True:
        if uuid in message_queues and not message_queues[uuid].empty():
            message_id, message = await message_queues[uuid].get()
            if uuid in connections:
                websocket = connections[uuid]
                await websocket.send_text(message)
                response = await websocket.receive_text()
                responses[message_id] = response
                response_events[message_id].set()
            else:
                print("WebSocket não conectado para UUID:", uuid)
        await asyncio.sleep(0.1)

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    connections[uuid] = websocket
    await websocket.accept()
    if uuid not in message_queues:
        message_queues[uuid] = asyncio.Queue()
    await process_message(uuid)

@app.post("/webhook/")
async def read_webhook(message: Message):
    target_uuid = message.uuid_user
    message_id = str(uuid.uuid4())
    response_events[message_id] = asyncio.Event()
    if target_uuid in connections:
        await message_queues[target_uuid].put((message_id, message.mensagem))
        await asyncio.wait_for(response_events[message_id].wait(), timeout=10)
        return {"response": responses.pop(message_id)}
    else:
        return {"response": "UUID não encontrado ou conexão não estabelecida"}

# Outras rotas e lógicas conforme necessário
