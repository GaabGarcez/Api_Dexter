from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
import logging
import uuid

app = FastAPI()

# Configuração de Logging
logging.basicConfig(level=logging.INFO)

connections = {}
message_queues = {}
responses = {}

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def handle_websocket_messages(websocket: WebSocket, uuid_user: str):
    while True:
        try:
            if uuid_user in message_queues and not message_queues[uuid_user].empty():
                message_info = await message_queues[uuid_user].get()
                await websocket.send_text(message_info['mensagem'])
                response_message = await websocket.receive_text()
                responses[message_info['message_id']] = response_message
            else:
                await asyncio.sleep(0.1)
        except Exception as e:
            logging.error(f"Erro na comunicação com o usuário {uuid_user}: {e}")
            break  # Sair do loop em caso de erro

@app.websocket("/connect/{uuid_user}")
async def websocket_endpoint(websocket: WebSocket, uuid_user: str):
    await websocket.accept()
    connections[uuid_user] = websocket
    message_queues[uuid_user] = asyncio.Queue()
    try:
        await handle_websocket_messages(websocket, uuid_user)
    except Exception as e:
        logging.error(f"Erro na conexão WebSocket com usuário {uuid_user}: {e}")
    finally:
        del connections[uuid_user]
        del message_queues[uuid_user]

@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid_user = message.uuid_user
    message_id = str(uuid.uuid4())

    if uuid_user in connections:
        if uuid_user not in message_queues:
            message_queues[uuid_user] = asyncio.Queue()
        await message_queues[uuid_user].put({"mensagem": message.mensagem, "message_id": message_id})
        
        # Aguardar a resposta
        while message_id not in responses:
            await asyncio.sleep(0.1)
        return {"response": responses.pop(message_id)}
    else:
        return {"response": "O Dexter não está sendo executado no seu servidor."}
