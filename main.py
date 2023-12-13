from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
import logging
import uuid

app = FastAPI()
logging.basicConfig(level=logging.DEBUG)

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.message_queues = {}
        self.responses = {}

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
            logging.info(f"Usuário {uuid_user} desconectado.")

    async def send_message(self, uuid_user: str, message: str, message_id: str):
        if uuid_user in self.active_connections:
            await self.message_queues[uuid_user].put({"mensagem": message, "message_id": message_id})
            while message_id not in self.responses:
                await asyncio.sleep(0.1)
            return self.responses.pop(message_id)
        else:
            return None

    def store_response(self, uuid_user: str, message_id: str, response: str):
        self.responses[message_id] = response

manager = ConnectionManager()

class Message(BaseModel):
    uuid_user: str
    mensagem: str

@app.websocket("/connect/{uuid_user}")
async def websocket_endpoint(websocket: WebSocket, uuid_user: str):
    await manager.connect(uuid_user, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.store_response(uuid_user, data)
    except Exception as e:
        logging.error(f"Erro na comunicação com o usuário {uuid_user}: {e}")
    finally:
        await manager.disconnect(uuid_user)

@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid_user = message.uuid_user
    message_id = str(uuid.uuid4())
    response = await manager.send_message(uuid_user, message.mensagem, message_id)
    if response:
        return {"response": response}
    else:
        logging.warning(f"Tentativa de enviar mensagem para usuário {uuid_user}, mas não está conectado.")
        return {"response": "O Dexter não está sendo executado no seu servidor."}
