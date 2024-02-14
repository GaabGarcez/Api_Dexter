from fastapi import FastAPI
from pydantic import BaseModel
import aiohttp

app = FastAPI()
connections = {}

class RequestData(BaseModel):
    uuid_user: str
    mensagem: str
    tipo: str

@app.post("/reativo_request")
async def make_request(data: RequestData):
    if data.uuid_user not in connections:
        return {"response": {"resposta": "A resposta não pode ser acessada pois o Dexter não está sendo executado no seu servidor."}}
    try:
        url = connections[data.uuid_user]
        # Utiliza aiohttp.ClientSession para fazer a requisição POST de forma assíncrona
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{url}/webhook", json={"mensagem": data.mensagem, "tipo": data.tipo}, timeout=60) as response:
                response_json = await response.json()
                return {"response": response_json}
    except aiohttp.ClientTimeout:
        # Trata o caso em que o request excedeu o tempo limite
        return {"response": {"resposta": "O pedido excedeu o tempo limite."}}
    except Exception as e:
        # Trata outros erros
        return {"response": {"resposta": "A resposta não pode ser acessada pois o Dexter não está sendo executado no seu servidor."}}

class ConnectData(BaseModel):
    uuid_user: str
    url: str

@app.post("/conectar")
async def connect(data: ConnectData):
    connections[data.uuid_user] = data.url
    print(f"Conectado: {data.uuid_user}, URL: {data.url}")

class AnalyzeConnection(BaseModel):
    uuid_user: str

@app.post("/deletar_cliente")
async def delete(data: AnalyzeConnection):
    connections.pop(data.uuid_user, None)
    return connections

@app.get("/clientes_conectados")
async def connected():
    return connections
