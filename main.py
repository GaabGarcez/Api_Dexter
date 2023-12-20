from fastapi import FastAPI, HTTPException
import requests
from pydantic import BaseModel

app = FastAPI()
connections = {}

class RequestData(BaseModel):
    uuid_user: str
    mensagem: str

@app.post("/request/")
async def make_request(data: RequestData):
    if data.uuid_user not in connections:
        return "Dexter não está em funcionamento neste servidor"
    
    ngrok_url = connections[data.uuid_user]
    response = requests.post(f"{ngrok_url}/webhook/", json={"mensagem": data.mensagem})
    return response.json()

class ConnectData(BaseModel):
    uuid_user: str
    ngrok_url: str

@app.post("/connect/")
async def connect(data: ConnectData):
    connections[data.uuid_user] = data.ngrok_url
    print(f"Conectado: {data.uuid_user}, URL: {data.ngrok_url}")

class DisconnectData(BaseModel):
    uuid_user: str

@app.post("/disconnect/")
async def disconnect(data: DisconnectData):
    if data.uuid_user in connections:
        print(f"Desconectado: {data.uuid_user}")
        connections.pop(data.uuid_user)

