from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Message(BaseModel):
    numero: str
    mensagem: str

@app.post("/webhook/")
async def read_webhook(message: Message):
    return {"response": f"{message.numero} - {message.mensagem} - Dexter é brabo!"}
