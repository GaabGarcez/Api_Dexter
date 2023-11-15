from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import requests
import asyncio  # Adicionado importação de asyncio
from collections import defaultdict

lock = asyncio.Lock()
app = FastAPI()
connections = {}
pending_messages = {}
message_queues = defaultdict(asyncio.Queue)

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def handle_websocket_messages(websocket: WebSocket, uuid: str):
    try:
        while True:
            if not message_queues[uuid].empty():
                message = await message_queues[uuid].get()
                await websocket.send_text(message)
                message_queues[uuid].task_done()
            else:
                await asyncio.sleep(0.1)  # Ajuste o tempo de espera conforme necessário
    except Exception as e:
        print(f"Erro ao lidar com mensagens WebSocket: {e}")


async def enqueue_message(uuid, message):
    await message_queues[uuid].put(message)


@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await lock.acquire()
    try:
        await websocket.accept()
        connections[uuid] = websocket
        await handle_websocket_messages(websocket, uuid)
    except Exception as e:
        print(f"Erro ao lidar com mensagens WebSocket: {e}")
    finally:
        del connections[uuid]
        lock.release()


@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid = message.uuid_user
    if uuid in connections:
        await enqueue_message(uuid, message.mensagem)
        return {"response": "Mensagem enfileirada com sucesso"}
    else:
        return {"response": "UUID não encontrado"}