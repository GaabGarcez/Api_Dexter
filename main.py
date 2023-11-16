from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
from collections import defaultdict

app = FastAPI()

connections = {}
message_queues = defaultdict(asyncio.Queue)
response_futures = {}  # Usando Futures para gerenciar respostas

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def handle_websocket_messages(websocket: WebSocket, uuid: str):
    while True:
        try:
            if not message_queues[uuid].empty():
                message_id, message = await message_queues[uuid].get()
                await websocket.send_text(message)
                response_futures[message_id] = asyncio.Future()
                # Aguarda a resposta e armazena no Future correspondente
            else:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Erro com WebSocket {uuid}: {e}")

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket
    try:
        await handle_websocket_messages(websocket, uuid)
    except Exception as e:
        print(f"Erro ao lidar com WebSocket {uuid}: {e}")
    finally:
        del connections[uuid]

@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid = message.uuid_user
    if uuid in connections:
        try:
            message_id = str(uuid.uuid4())
            await message_queues[uuid].put((message_id, message.mensagem))
            response_future = response_futures[message_id] = asyncio.Future()
            return {"response": await asyncio.wait_for(response_future, timeout=30)}
        except asyncio.TimeoutError:
            return {"response": "Timeout esperando resposta do servidor local."}
        except Exception as e:
            return {"response": f"Erro ao processar a mensagem: {e}"}
    else:
        return {"response": "UUID não encontrado ou conexão não estabelecida"}
