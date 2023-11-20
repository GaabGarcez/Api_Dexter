from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
import uuid
import starlette
import websockets

app = FastAPI()

connections = {}
message_queues = {}
responses = {}

class Message(BaseModel):
    uuid_user: str
    mensagem: str

async def process_message(websocket: WebSocket, uuid: str):
    while True:
        if not message_queues[uuid].empty():
            message_id, message = await message_queues[uuid].get()
            await websocket.send_text(f"{message_id}:{message}")  # Envio de message_id com a mensagem
            response = await websocket.receive_text()
            responses[message_id] = response  # Associa a resposta ao identificador da mensagem
        else:
            await asyncio.sleep(0.1)

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket
    if uuid not in message_queues:
        message_queues[uuid] = asyncio.Queue()

    try:
        await process_message(websocket, uuid)
    except websockets.exceptions.ConnectionClosedOK:
        # Remover a conexão do dicionário quando ela é fechada
        connections.pop(uuid, None)
    except starlette.websockets.WebSocketDisconnect as e:
        # Lidar com desconexão WebSocket
        print(f"WebSocket Disconnect Error: {e}")
        connections.pop(uuid, None)


@app.post("/webhook/")
async def read_webhook(message: Message):
    target_uuid = message.uuid_user
    message_id = str(uuid.uuid4())  # Identificador único para a mensagem
    if target_uuid in connections:
        await message_queues[target_uuid].put((message_id, message.mensagem))
        while message_id not in responses:
            await asyncio.sleep(0.1)
        response = responses.pop(message_id)
        response_content = response.split(":", 1)[1] if ":" in response else response  # Extrair apenas o conteúdo da resposta
        return {"response": response_content}
    else:
        return {"response": "UUID não encontrado ou conexão não estabelecida"}
