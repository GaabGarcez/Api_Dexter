from fastapi import FastAPI
from fastapi_socketio import SocketManager
from pydantic import BaseModel
import asyncio
import logging
import uuid

app = FastAPI()
sio = SocketManager(app=app)
logging.basicConfig(level=logging.DEBUG)

connections = {}  # Mapeia UUIDs de usuários para SIDs do Socket.IO
pending_responses = {}  # Mapeia message_ids para futuros de resposta

class Message(BaseModel):
    uuid_user: str
    mensagem: str

@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid_user = message.uuid_user
    message_id = str(uuid.uuid4())

    if uuid_user in connections:
        response_future = asyncio.get_event_loop().create_future()
        pending_responses[message_id] = response_future
        await sio.emit('message_event', {"mensagem": message.mensagem, "message_id": message_id}, to=connections[uuid_user])

        try:
            response = await asyncio.wait_for(response_future, timeout=30)  # Aguarda a resposta por 30 segundos
            return {"response": response}
        except asyncio.TimeoutError:
            return {"response": "Timeout na espera pela resposta."}
    else:
        return {"response": "Usuário não conectado ou não encontrado."}

@sio.on('message_response')
async def handle_message_response(sid, data):
    message_id = data['message_id']
    if message_id in pending_responses:
        pending_responses[message_id].set_result(data['resposta'])
        del pending_responses[message_id]
