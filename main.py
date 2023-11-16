from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
from collections import defaultdict

app = FastAPI()

connections = {}
message_queues = defaultdict(asyncio.Queue)

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def handle_websocket_messages(websocket: WebSocket, uuid: str):
    while True:
        try:
            if not message_queues[uuid].empty():
                message = await message_queues[uuid].get()
                await websocket.send_text(message)
            else:
                await asyncio.sleep(0.1)  # Reduzindo o atraso para melhor responsividade
        except asyncio.CancelledError:
            break  # Encerrando a loop corretamente na desconexão
        except Exception as e:
            print(f"Erro com WebSocket {uuid}: {e}")

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    print(f"WebSocket conectado: {uuid}")
    connections[uuid] = websocket
    try:
        await handle_websocket_messages(websocket, uuid)
    except Exception as e:
        print(f"Erro ao lidar com WebSocket {uuid}: {e}")
    finally:
        print(f"WebSocket desconectado: {uuid}")
        del connections[uuid]

@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid = message.uuid_user
    if uuid in connections:
        try:
            await message_queues[uuid].put(message.mensagem)
            return {"response": "Mensagem enfileirada"}
        except Exception as e:
            return {"response": f"Erro ao enfileirar mensagem: {e}"}
    else:
        return {"response": "UUID não encontrado ou conexão não estabelecida"}
