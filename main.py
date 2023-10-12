from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import requests
import asyncio  # Adicionado importação de asyncio

app = FastAPI()

# Tabela de associação para mapear UUID para conexão WebSocket e mensagens pendentes
connections = {}
pending_messages = {}

class Message(BaseModel):
    numero: str
    mensagem: str

async def handle_websocket_messages(websocket: WebSocket, uuid: str):
    try:
        while True:
            if uuid in pending_messages:
                message = pending_messages.pop(uuid)
                await websocket.send_text(message)
            else:
                await asyncio.sleep(1)  # Adicione um pequeno atraso para evitar uso excessivo de CPU
    except:
        pass

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket
    try:
        await handle_websocket_messages(websocket, uuid)
    except Exception as e:
        print(f"Erro ao lidar com mensagens WebSocket: {e}")
    finally:
        del connections[uuid]

# ... (restante do código)



@app.post("/webhook/")
async def read_webhook(message: Message):
    response = requests.post('https://xkit-1dzl-gome.n7c.xano.io/api:fbhumpeF/dexter_validacao', data={"numero": message.numero}, verify=False)

    data = response.json()

    if "Seu número não está cadastrado!" in data:
        return {"response": "Seu número não está cadastrado!"}
    
    uuid = data  # O Xano retorna o UUID diretamente

    # Verifique se temos uma conexão WebSocket para esse UUID
    if uuid in connections:
        websocket = connections[uuid]
        await websocket.send_text(message.mensagem)  # Envie a mensagem para o servidor local
        response_message = await websocket.receive_text()  # Aguarde a resposta do servidor local
        return {"response": response_message}
    else:
        return {"response": "O dexter não está sendo executado no seu servidor."}
