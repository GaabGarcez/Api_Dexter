from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

VERIFY_TOKEN = "SEU_TOKEN_DE_VERIFICAÇÃO"

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    # Processar a notificação do evento aqui
    return {"status": "success"}

@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return {"hub.challenge": challenge}
        else:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        raise HTTPException(status_code=400, detail="Bad Request")
