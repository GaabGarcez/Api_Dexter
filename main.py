from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import requests

app = FastAPI()

# Tabela de associação para mapear UUID para conexão WebSocket
connections = {}

class Message(BaseModel):
    numero: str
    mensagem: str

@app.websocket("/connect/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    connections[uuid] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            # Aqui você pode processar a mensagem recebida se necessário
    except:
        del connections[uuid]

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
        await websocket.send_text(message.mensagem)
        response = await websocket.receive_text()
        return {"response": f"{response}"}
    else:
        return {"response": "O dexter não está sendo executado no seu servidor."}
