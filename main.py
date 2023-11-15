from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
from collections import defaultdict
import uuid

app = FastAPI()

connections = {}
message_queues = defaultdict(asyncio.Queue)
responses = {}

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def handle_websocket_messages(websocket: WebSocket, uuid_str: str):
    try:
        while True:
            if not message_queues[uuid_str].empty():
                message_id, message = await message_queues[uuid_str].get()
                await websocket.send_text(message)
                response = await websocket.receive_text()
                responses[message_id] = response
                message_queues[uuid_str].task_done()
            else:
                await asyncio.sleep(0.1)
    except Exception as e:
        print(f"Erro ao lidar com mensagens WebSocket: {e}")

async def enqueue_message(uuid_str, message):
    message_id = str(uuid.uuid4())  # Gera um identificador único para a mensagem
    await message_queues[uuid_str].put((message_id, message))
    return message_id

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid_str: str):
    await websocket.accept()
    connections[uuid_str] = websocket
    try:
        await handle_websocket_messages(websocket, uuid_str)
    except Exception as e:
        print(f"Erro ao lidar com mensagens WebSocket: {e}")
    finally:
        del connections[uuid_str]

@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid_str = message.uuid_user
    if uuid_str in connections:
        try:
            message_id = await enqueue_message(uuid_str, message.mensagem)
            # Aguardar aqui pela resposta e retorná-la
            while message_id not in responses:
                await asyncio.sleep(0.1)  # Ajuste o tempo de espera conforme necessário
            return {"response": responses.pop(message_id)}
        except Exception as e:
            return {"response": f"Erro ao processar a mensagem: {e}"}
    else:
        return {"response": "UUID não encontrado ou conexão não estabelecida"}
