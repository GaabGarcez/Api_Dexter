from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
from collections import defaultdict

app = FastAPI()

# Estruturas para gerenciar conexões, filas de mensagens, e callbacks de respostas
connections = {}
message_queues = defaultdict(asyncio.Queue)
response_callbacks = {}

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def handle_websocket_messages(websocket: WebSocket, uuid: str):
    try:
        while True:
            if not message_queues[uuid].empty():
                message = await message_queues[uuid].get()
                await websocket.send_text(message)
                response = await websocket.receive_text()
                if uuid in response_callbacks:
                    response_callbacks[uuid](response)  # Chama o callback com a resposta
                message_queues[uuid].task_done()
            else:
                await asyncio.sleep(0.1)
    except Exception as e:
        print(f"Erro ao lidar com mensagens WebSocket: {e}")

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket
    try:
        await handle_websocket_messages(websocket, uuid)
    except Exception as e:
        print(f"Erro ao lidar com mensagens WebSocket: {e}")
    finally:
        del connections[uuid]

@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid = message.uuid_user
    if uuid in connections:
        await message_queues[uuid].put(message.mensagem)
        response_future = asyncio.Future()
        response_callbacks[uuid] = response_future.set_result
        try:
            response = await asyncio.wait_for(response_future, timeout=30)  # Espera a resposta por até 30 segundos
            return {"response": response}
        except asyncio.TimeoutError:
            return {"response": "Timeout esperando resposta do servidor local."}
        finally:
            response_callbacks.pop(uuid, None)
    else:
        return {"response": "UUID não encontrado."}
