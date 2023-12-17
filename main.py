import socketio
from fastapi import FastAPI, Request

sio = socketio.AsyncServer(async_mode='asgi')
app = FastAPI()
sio.attach(app)

connections = {}  # Dicionário para mapear IDs personalizados para SIDs do Socket.IO

@sio.event
async def connect(sid, environ):
    print(f'Cliente conectado com SID: {sid}')

@sio.event
async def disconnect(sid):
    print(f'Cliente desconectado com SID: {sid}')
    # Remove o SID do mapeamento ao desconectar
    for key, value in list(connections.items()):
        if value == sid:
            del connections[key]

@sio.event
async def registrar_id(sid, data):
    meu_id = data['meu_id']
    connections[meu_id] = sid  # Mapeia o ID personalizado para o SID
    print(f'O ID personalizado do cliente {sid} é {meu_id}')

@app.get("/clientes_conectados")
async def get_connected_clients(request: Request):
    return connections

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
