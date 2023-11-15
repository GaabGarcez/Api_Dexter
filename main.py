from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
from collections import defaultdict

app = FastAPI()

connections = {}
message_queues = defaultdict(asyncio.Queue)
response_callbacks = {}  # Usando a abordagem de callback do código antigo

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def handle_websocket_messages(websocket: WebSocket, uuid_str: str):
    try:
        while True:
            if not message_queues[uuid_str].empty():
                message = await message_queues[uuid_str].get()
                await websocket.send_text(message)
                response = await websocket.receive_text()
                if uuid_str in response_callbacks:
                    response_callbacks[uuid_str](response)  # Chama o callback com a resposta
                message_queues[uuid_str].task_done()
            else:
                await asyncio.sleep(0.1)
    except Exception as e:
        print(f"Erro ao lidar com mensagens WebSocket: {e}")

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
        await message_queues[uuid_str].put(message.mensagem)
        response_future = asyncio.Future()
        response_callbacks[uuid_str] = response_future.set_result
        try:
            response = await asyncio.wait_for(response_future, timeout=30)
            return {"response": response}
        except asyncio.TimeoutError:
            return {"response": "Timeout esperando resposta do servidor local."}
        finally:
            response_callbacks.pop(uuid_str, None)
    else:
        return {"response": "UUID não encontrado ou conexão não estabelecida"}
