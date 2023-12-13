from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
import logging
import uuid

app = FastAPI()
logging.basicConfig(level=logging.DEBUG)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.message_queues: dict[str, asyncio.Queue] = {}
        self.responses: dict[str, str] = {}

    async def connect(self, uuid_user: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[uuid_user] = websocket
        self.message_queues[uuid_user] = asyncio.Queue()
        logging.info(f"Usuário {uuid_user} conectado.")

    async def disconnect(self, uuid_user: str):
        if uuid_user in self.active_connections:
            await self.active_connections[uuid_user].close()
            del self.active_connections[uuid_user]
            del self.message_queues[uuid_user]
            self.responses.pop(uuid_user, None)
            logging.info(f"Usuário {uuid_user} desconectado.")

    async def send_personal_message(self, message: str, uuid_user: str):
        if uuid_user in self.active_connections:
            await self.active_connections[uuid_user].send_text(message)

    async def receive_personal_message(self, uuid_user: str):
        if uuid_user in self.active_connections:
            response_message = await self.active_connections[uuid_user].receive_text()
            self.responses[uuid_user] = response_message
            return response_message
    async def is_connected(self, uuid_user: str):
        websocket = self.active_connections.get(uuid_user)
        return websocket and not websocket.closed

manager = ConnectionManager()

class Message(BaseModel):
    uuid_user: str
    mensagem: str

@app.websocket("/connect/{uuid_user}")
async def websocket_endpoint(websocket: WebSocket, uuid_user: str):
    await manager.connect(uuid_user, websocket)
    try:
        while True:
            if not manager.message_queues[uuid_user].empty():
                message_info = await manager.message_queues[uuid_user].get()
                await manager.send_personal_message(message_info['mensagem'], uuid_user)
                response_message = await manager.receive_personal_message(uuid_user)
                manager.responses[message_info['message_id']] = response_message
            else:
                await asyncio.sleep(0.1)
    except Exception as e:
        logging.error(f"Erro na comunicação com o usuário {uuid_user}: {e}")
    finally:
        await manager.disconnect(uuid_user)

@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid_user = message.uuid_user
    message_id = str(uuid.uuid4())

    if await manager.is_connected(uuid_user):
        await manager.message_queues[uuid_user].put({"mensagem": message.mensagem, "message_id": message_id})
        while message_id not in manager.responses:
            await asyncio.sleep(0.1)
        return {"response": manager.responses.pop(message_id)}
    else:
        logging.warning(f"Tentativa de enviar mensagem para usuário {uuid_user}, mas o Dexter está desligado.")
        return {"response": "O Dexter não está sendo executado no seu servidor."}
