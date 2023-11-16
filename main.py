from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
import uuid

app = FastAPI()

connections = {}
message_queues = {}
response_futures = {}  # Dicionário para armazenar os futures das respostas

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def send_message(websocket: WebSocket, message: str, message_id: str):
    await websocket.send_text(message)
    response = await websocket.receive_text()
    response_futures[message_id].set_result(response)

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    if uuid not in message_queues:
        message_queues[uuid] = asyncio.Queue()
    connections[uuid] = websocket
    while True:
        if not message_queues[uuid].empty():
            message_id, message = await message_queues[uuid].get()
            response_futures[message_id] = asyncio.Future()
            asyncio.create_task(send_message(websocket, message, message_id))
        else:
            await asyncio.sleep(0.1)

@app.post("/webhook/")
async def read_webhook(message: Message):
    target_uuid = message.uuid_user
    unique_message_id = str(uuid.uuid4())
    if target_uuid in connections:
        try:
            await message_queues[target_uuid].put((unique_message_id, message.mensagem))
            response_future = response_futures[unique_message_id] = asyncio.Future()
            response = await response_future
            return {"response": response}
        except Exception as e:
            return {"response": f"Erro ao processar a mensagem: {e}"}
    else:
        return {"response": "UUID não encontrado ou conexão não estabelecida"}
