from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio

app = FastAPI()

connections = {}
pending_messages = {}  # Inicializa o dicionário de mensagens pendentes
message_events = {}

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def handle_websocket_messages(websocket: WebSocket, uuid: str):
    while True:
        await message_events[uuid].wait()  # Espera até que uma mensagem esteja disponível
        message = pending_messages.pop(uuid)
        await websocket.send_text(message)
        message_events[uuid].clear()  # Reseta o evento

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket
    message_events[uuid] = asyncio.Event()  # Cria um novo Event para esta conexão
    try:
        await handle_websocket_messages(websocket, uuid)
    except Exception as e:
        print(f"Erro ao lidar com mensagens WebSocket: {e}")
    finally:
        del connections[uuid]
        del message_events[uuid]  # Remove o evento associado

@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid = message.uuid_user  
    if uuid in connections:
        websocket = connections[uuid]
        try:
            pending_messages[uuid] = message.mensagem
            message_events[uuid].set()  # Sinaliza que uma nova mensagem está disponível
            return {"response": "Mensagem enviada"}
        except Exception as e:
            return {"response": f"Erro ao enviar mensagem: {e}"}
    else:
        return {"response": "UUID não encontrado ou conexão não estabelecida"}
