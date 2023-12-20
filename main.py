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

@app.post("/connect/")
async def connect(uuid_user: str, ngrok_url: str):
    connections[uuid_user] = ngrok_url
    print(f"Conectado: {uuid_user}, URL: {ngrok_url}")

@app.post("/disconnect/")
async def disconnect(uuid_user: str):
    if uuid_user in connections:
        print(f"Desconectado: {uuid_user}")
        connections.pop(uuid_user)
