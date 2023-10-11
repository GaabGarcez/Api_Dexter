from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

VERIFY_TOKEN = "EABjyeHmZA4e4BO1wyFvCEcPuOQM1CMp5sVj9fDWezucyJBhOzpdpcAPHW8WZCHN3OfZCPu5G1cHFNZCx61iiB3Y2wYDU6YKCeVViR7nkfgfFavXEZC7x3SDGgfTq5S0fgZAz3aRnkplnIUD2v5wELyEec3K15YP7DX5htPtV19Rn7ZCNLK3D5otFsZBFVDJbjZBfnSKydjEL7tdvz5oxKX3jw8VmybacZD"

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
