from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
import uuid

app = FastAPI()

connections = {}
message_queues = {}
responses = {}
processing = set()  # Conjunto para rastrear quais UUIDs estão processando mensagens

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def enqueue_message(target_uuid: str, message: str):
    message_id = str(uuid.uuid4())
    if target_uuid not in message_queues:
        message_queues[target_uuid] = asyncio.Queue()
    await message_queues[target_uuid].put((message_id, message))
    return message_id

async def process_next_message(target_uuid: str):
    if target_uuid in connections and not message_queues[target_uuid].empty() and target_uuid not in processing:
        processing.add(target_uuid)
        websocket = connections[target_uuid]
        message_id, message = await message_queues[target_uuid].get()
        await websocket.send_text(message)
        response = await websocket.receive_text()
        responses[message_id] = response
        processing.remove(target_uuid)

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket
    # Processa mensagens assim que a conexão é estabelecida
    asyncio.create_task(process_next_message(uuid))

@app.post("/webhook/")
async def read_webhook(message: Message):
    target_uuid = message.uuid_user
    if target_uuid in connections:
        message_id = await enqueue_message(target_uuid, message.mensagem)
        asyncio.create_task(process_next_message(target_uuid))
        while message_id not in responses:
            await asyncio.sleep(0.1)
        return {"response": responses.pop(message_id)}
    else:
        return {"response": "O Dexter não está sendo executado no seu servidor."}
