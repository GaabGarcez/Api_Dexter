from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio

app = FastAPI()

connections = {}
message_queues = {}

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def handle_websocket_messages(websocket: WebSocket, uuid: str):
    while True:
        if uuid in message_queues and not message_queues[uuid].empty():
            message = await message_queues[uuid].get()
            await websocket.send_text(message)
        else:
            await asyncio.sleep(0.1)  # Pequeno atraso para evitar uso excessivo de CPU

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket
    message_queues[uuid] = asyncio.Queue()
    try:
        await handle_websocket_messages(websocket, uuid)
    except Exception as e:
        print(f"Erro ao lidar com mensagens WebSocket: {e}")
    finally:
        del connections[uuid]
        del message_queues[uuid]

@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid = message.uuid_user

    if uuid in connections:
        if uuid not in message_queues:
            message_queues[uuid] = asyncio.Queue()
        await message_queues[uuid].put(message.mensagem)
        
        # Esperando a resposta do servidor local
        websocket = connections[uuid]
        response_message = await websocket.receive_text()
        return {"response": response_message}
    else:
        return {"response": "O Dexter não está sendo executado no seu servidor."}
