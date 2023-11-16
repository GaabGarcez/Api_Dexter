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

async def enqueue_message(target_uuid: str, message: str):
    message_id = str(uuid.uuid4())
    if target_uuid not in message_queues:
        message_queues[target_uuid] = asyncio.Queue()
    await message_queues[target_uuid].put((message_id, message))
    return message_id

async def process_messages():
    while True:
        for uuid, queue in message_queues.items():
            if not queue.empty() and uuid in connections:
                message_id, message = await queue.get()
                websocket = connections[uuid]
                await websocket.send_text(message)
                response = await websocket.receive_text()
                responses[message_id] = response
        await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_messages())

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket

@app.post("/webhook/")
async def read_webhook(message: Message):
    target_uuid = message.uuid_user
    if target_uuid in connections:
        message_id = await enqueue_message(target_uuid, message.mensagem)
        while message_id not in responses:
            await asyncio.sleep(0.1)
        return {"response": responses.pop(message_id)}
    else:
        return {"response": "O Dexter não está sendo executado no seu servidor."}
