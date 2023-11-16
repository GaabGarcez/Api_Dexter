from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio

app = FastAPI()

connections = {}
response_futures = {}  # Para gerenciar as respostas

class Message(BaseModel):
    uuid_user: str
    mensagem: str

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, uuid: str):
        await websocket.accept()
        self.active_connections[uuid] = websocket

    def disconnect(self, uuid: str):
        if uuid in self.active_connections:
            del self.active_connections[uuid]

    async def send_message(self, uuid: str, message: str):
        if uuid in self.active_connections:
            websocket = self.active_connections[uuid]
            await websocket.send_text(message)
            return await websocket.receive_text()  # Aguardar a resposta

manager = ConnectionManager()

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await manager.connect(websocket, uuid)
    try:
        while True:
            await asyncio.sleep(1)  # Mantém a conexão ativa
    except WebSocketDisconnect:
        manager.disconnect(uuid)

@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid = message.uuid_user
    try:
        response = await manager.send_message(uuid, message.mensagem)
        return {"response": response}  # Retorna a resposta do WebSocket local
    except Exception as e:
        return {"response": f"Erro ao enviar mensagem: {e}"}
