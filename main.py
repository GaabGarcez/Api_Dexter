from fastapi import FastAPI, WebSocket, HTTPException
from starlette.websockets import WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import logging
import uuid
import time

app = FastAPI()
logging.basicConfig(level=logging.DEBUG)  # DEBUG para mais detalhes

connections = {}
message_queues = {}
responses = {}
last_ping = {}

class Message(BaseModel):
    uuid_user: str
    mensagem: str

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(print_connection_details())
    asyncio.create_task(send_ping())

async def send_ping():
    while True:
        current_time = time.time()
        for uuid_user, queue in message_queues.items():
            if current_time - last_ping.get(uuid_user, 0) > 20:  # Ping a cada 20 segundos
                await queue.put("ping")
                last_ping[uuid_user] = current_time
        await asyncio.sleep(5)  # Intervalo de verificação

async def print_connection_details():
    while True:
        for uuid_user, websocket in connections.items():
            # Tentativa de obter informações adicionais da conexão
            client_state = "ativo" if not websocket.client_state == WebSocketDisconnect else "desconectado"
            try:
                client_host = websocket.client.host
                client_port = websocket.client.port
            except AttributeError:
                client_host, client_port = "Indisponível", "Indisponível"

            logging.info(f"Usuário: {uuid_user}, Estado: {client_state}, Endereço: {client_host}:{client_port}")

        await asyncio.sleep(120)  # Espera por 2 minuto

async def handle_websocket_messages(websocket: WebSocket, uuid_user: str):
    while True:
        try:
            if uuid_user in message_queues and not message_queues[uuid_user].empty():
                message_info = await message_queues[uuid_user].get()
                if message_info == "ping":
                    await websocket.send_text("ping")  # Envio prioritário de ping
                else:
                    # Processamento normal de mensagens
                    logging.info(f"Tentando enviar mensagem para {uuid_user}, estado da conexão: {websocket.client_state}")
                    await websocket.send_text(message_info['mensagem'])
                    response_message = await websocket.receive_text()
                    responses[message_info['message_id']] = response_message
            else:
                await asyncio.sleep(0.1)
        except WebSocketDisconnect:
            logging.info(f"WebSocketDisconnect: Conexão com {uuid_user} foi fechada.")
            break
        except Exception as e:
            logging.error(f"Erro ao enviar mensagem para {uuid_user}: {e}")
            break

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

    if uuid_user in connections and connections[uuid_user].application_state != "disconnected":
        if uuid_user not in message_queues:
            message_queues[uuid_user] = asyncio.Queue()
        await message_queues[uuid_user].put({"mensagem": message.mensagem, "message_id": message_id})
        
        # Aguardar a resposta
        while message_id not in responses:
            await asyncio.sleep(0.1)
        return {"response": responses.pop(message_id)}
    else:
        return {"response": "O Dexter não está sendo executado no seu servidor."}

@app.post("/disconnect/{uuid_user}")
async def disconnect_client(uuid_user: str):
    if uuid_user in connections:
        await connections[uuid_user].close()
        connections.pop(uuid_user, None)
        message_queues.pop(uuid_user, None)
        responses.pop(uuid_user, None)
        logging.info(f"Usuário {uuid_user} desconectado.")
        return {"status": "Disconnected"}
    else:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")