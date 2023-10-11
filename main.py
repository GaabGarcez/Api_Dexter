from fastapi import FastAPI, Request, HTTPException
from typing import Optional

app = FastAPI()

VERIFY_TOKEN = "27032001"  # Substitua por seu token de verificação

@app.get("/webhook")
async def verify(request: Request):
    # Obter parâmetros da string de consulta
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # Verificar se o token de verificação corresponde
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return {"hub.challenge": challenge}
        else:
            raise HTTPException(status_code=403, detail="Token de verificação não corresponde")
    else:
        raise HTTPException(status_code=403, detail="Parâmetros ausentes")

@app.post("/webhook")
async def handle_webhook(request: Request):
    # Aqui, você pode processar o payload da notificação de evento
    # Por enquanto, apenas respondemos com um 200 OK
    return {"status": "received"}