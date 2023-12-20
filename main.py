from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()
connections = {}

class RequestData(BaseModel):
    uuid_user: str
    mensagem: str

@app.post("/request/")
async def make_request(data: RequestData):
    if data.uuid_user not in connections:
        return "Dexter não está em funcionamento neste servidor"
    
    try:
        ngrok_url = connections[data.uuid_user]
        response = requests.post(f"{ngrok_url}/webhook/", json={"mensagem": data.mensagem})
        return response.json()
    except Exception as e:
        # Remover a conexão inativa e notificar o usuário
        connections.pop(data.uuid_user, None)
        return "Dexter não está em funcionamento neste servidor"

class ConnectData(BaseModel):
    uuid_user: str
    ngrok_url: str

@app.post("/connect/")
async def connect(data: ConnectData):
    connections[data.uuid_user] = data.ngrok_url
    print(f"Conectado: {data.uuid_user}, URL: {data.ngrok_url}")