from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()
connections = {}

@app.post("/connect/")
async def connect(uuid_user: str, ngrok_url: str):
    connections[uuid_user] = ngrok_url
    return {"message": "Conexão registrada"}

@app.post("/disconnect/")
async def disconnect(uuid_user: str):
    connections.pop(uuid_user, None)
    return {"message": "Conexão removida"}

@app.post("/request/")
async def make_request(uuid_user: str, mensagem: str):
    if uuid_user not in connections:
        return "Dextr não está em funcionamento neste servidor"
    
    ngrok_url = connections[uuid_user]
    response = requests.post(f"{ngrok_url}/webhook/", json={"mensagem": mensagem})
    return response.json()
