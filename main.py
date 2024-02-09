from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()
connections = {}

class RequestData(BaseModel):
    uuid_user: str
    mensagem: str
    historico: str

@app.post("/request/")
async def make_request(data: RequestData):
    if data.uuid_user not in connections:
        return {"response": {"resposta": "O Dexter não está sendo executado no seu servidor."}}
    
    try:
        url = connections[data.uuid_user]
        response = requests.post(f"{url}/webhook/", json={"mensagem": data.mensagem})
        return {"response": response.json()}
    except Exception as e:
        connections.pop(data.uuid_user, None)
        return {"response": {"resposta": "O Dexter não está sendo executado no seu servidor."}}

class ConnectData(BaseModel):
    uuid_user: str
    url: str

@app.post("/connect/")
async def connect(data: ConnectData):
    connections[data.uuid_user] = data.url
    print(f"Conectado: {data.uuid_user}, URL: {data.url}")
