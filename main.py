from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
import uuid

app = FastAPI()

connections = {}
responses = {}

class Message(BaseModel):
    uuid_user: str
    mensagem: str

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket

@app.post("/webhook/")
async def read_webhook(message: Message):
    target_uuid = message.uuid_user
    if target_uuid in connections:
        message_id = str(uuid.uuid4())
        await connections[target_uuid].send_text(message.mensagem)
        response = await connections[target_uuid].receive_text()
        return {"response": response}
    else:
        return {"response": "O Dexter não está sendo executado no seu servidor."}
