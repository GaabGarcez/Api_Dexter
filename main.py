from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio  
app = FastAPI()

connections = {}
pending_messages = {}

class Message(BaseModel):
    uuid_user: str
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

@app.post("/webhook/")
async def read_webhook(message: Message):
    
    
    uuid = message.uuid_user  # O Xano retorna o UUID diretamente

    # Verifique se temos uma conexão WebSocket para esse UUID
    if uuid in connections:
        websocket = connections[uuid]
        try:
            await websocket.send_text(message.mensagem)  # Envie a mensagem para o servidor local
            response_message = await websocket.receive_text()  # Aguarde a resposta do servidor local
            return {"response": response_message}
        except Exception as e:
            # Se ocorrer uma exceção ao tentar enviar/receber uma mensagem, assumimos que a conexão foi fechada
            return {"response": "O Dexter não está sendo executado no seu servidor."}
    else:
        return {"response": "O Dexter não está sendo executado no seu servidor."}