from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
import uuid
import logging

app = FastAPI()

connections = {}
message_queues = {}
responses = {}
event_flags = {}

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def handle_websocket_messages(websocket: WebSocket, uuid_user: str):
    while True:
        if uuid_user in message_queues and not message_queues[uuid_user].empty():
            message_info = await message_queues[uuid_user].get()
            await websocket.send_text(message_info['mensagem'])
            response_message = await websocket.receive_text()
            responses[message_info['message_id']] = response_message
            event_flags[message_info['message_id']].set()
        else:
            await asyncio.sleep(0.1)

@app.websocket("/connect/{uuid_user}")
async def websocket_endpoint(websocket: WebSocket, uuid_user: str):
    await websocket.accept()
    connections[uuid_user] = websocket
    message_queues[uuid_user] = asyncio.Queue()
    try:
        await handle_websocket_messages(websocket, uuid_user)
    except Exception as e:
        logging.error(f"Erro ao lidar com mensagens WebSocket: {e}")
    finally:
        del connections[uuid_user]
        del message_queues[uuid_user]

@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid_user = message.uuid_user
    message_id = str(uuid.uuid4())

    if uuid_user in connections:
        if uuid_user not in message_queues:
            message_queues[uuid_user] = asyncio.Queue()
        event_flags[message_id] = asyncio.Event()
        await message_queues[uuid_user].put({"mensagem": message.mensagem, "message_id": message_id})
        
        # Aguarda até que a resposta esteja disponível
        await event_flags[message_id].wait()
        return {"response": responses.pop(message_id)}
    else:
        return {"response": "O Dexter não está sendo executado no seu servidor."}
