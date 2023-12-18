from fastapi import FastAPI
import threading
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from twisted.internet import reactor
import json
import logging
from pydantic import BaseModel
import asyncio
import logging
import uuid

app = FastAPI()
class Message(BaseModel):
    uuid_user: str
    mensagem: str
# Fábrica do Servidor WebSocket
class MeuServidorFactory(WebSocketServerFactory):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clients = {}

    def register(self, client, client_id):
        self.clients[client_id] = client
        logging.info(f"Cliente {client_id} registrado.")

    def unregister(self, client_id):
        if client_id in self.clients:
            del self.clients[client_id]
            logging.info(f"Cliente {client_id} desregistrado.")

    def encaminhar_mensagem_para_cliente(self, id_cliente, mensagem):
        if id_cliente in self.clients:
            cliente = self.clients[id_cliente]
            cliente.sendMessage(json.dumps(mensagem).encode('utf8'))
            logging.info(f"Mensagem encaminhada para {id_cliente}.")
            return True
        else:
            logging.info(f"Nenhum cliente conectado com o ID {id_cliente}.")
            return False

# Protocolo do Servidor WebSocket
class MeuServidorProtocolo(WebSocketServerProtocol):

    def onOpen(self):
        logging.info("Conexão WebSocket aberta.")

    def onMessage(self, payload, isBinary):
        if not isBinary:
            mensagem = json.loads(payload.decode('utf8'))

            if mensagem.get("tipo") == "id":
                self.uuid_user = mensagem['id']
                self.factory.register(self, self.uuid_user)
                logging.info(f"ID único recebido: {self.uuid_user}")
            else:
                # Outras mensagens podem ser tratadas aqui
                pass

    def onClose(self, wasClean, code, reason):
        if hasattr(self, 'uuid_user'):
            self.factory.unregister(self.uuid_user)
            logging.info(f"Conexão WebSocket fechada para {self.uuid_user}: {reason}")

# Inicialização do servidor WebSocket
@app.on_event("startup")
def start_websocket_server():
    logging.basicConfig(level=logging.INFO)
    endereco_servidor = "ws://0.0.0.0:9000"
    global factory
    factory = MeuServidorFactory(endereco_servidor)
    factory.protocol = MeuServidorProtocolo
    reactor.listenTCP(9000, factory)

# Endpoint para enviar mensagens para clientes WebSocket
@app.post("/enviar_para_cliente/{id_cliente}")
async def enviar_para_cliente(id_cliente: str, mensagem: dict):
    factory.encaminhar_mensagem_para_cliente(id_cliente, mensagem)
    return {"status": "Mensagem enviada"}


@app.post("/webhook/")
async def read_webhook(message: Message):
    uuid_user = message.uuid_user
    mensagem_user = message.mensagem

    if factory.encaminhar_mensagem_para_cliente(uuid_user, mensagem_user):
        return {"status": f"Mensagem enviada para o cliente {uuid_user}, com o conteúdo: {mensagem_user}"}
    else:
        return {"status": "Nenhum cliente conectado com o ID fornecido."}