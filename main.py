from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

VERIFY_TOKEN = "EABjyeHmZA4e4BOzjLT0U0AgVRSyTt7P1qcQMT2IoTGCFdqHQP4sNYLnPyf8NmXBCJNIvJ6VMeDTpEGejNaUO5iFsa3ZAOtSLx0EhUHHuPOh6zTke6mUNZAoPeYQ8MYHyx5Pu8OGRDMZB4lo5y6m2oy8nno6lPk688XmuYLCHMB5DO34Ow2v3lqcUMBa28IVW"

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
