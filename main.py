from fastapi import FastAPI, Request, HTTPException, Depends
from typing import Optional
import requests
import json

app = FastAPI()

# Tokens (ajuste conforme necessário)
WHATSAPP_TOKEN = "EABjyeHmZA4e4BOzjLT0U0AgVRSyTt7P1qcQMT2IoTGCFdqHQP4sNYLnPyf8NmXBCJNIvJ6VMeDTpEGejNaUO5iFsa3ZAOtSLx0EhUHHuPOh6zTke6mUNZAoPeYQ8MYHyx5Pu8OGRDMZB4lo5y6m2oy8nno6lPk688XmuYLCHMB5DO34Ow2v3lqcUMBa28IVW"
VERIFY_TOKEN = "ZEUX"


@app.post("/webhook/")
async def webhook(request: Request):
    body = await request.json()

    # Verifique a mensagem do webhook recebida
    print(json.dumps(body, indent=2))

    if "object" in body:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [{}])[0]

        if all([
            entry,
            changes,
            value,
            messages
        ]):
            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            from_number = messages.get("from")
            msg_body = messages.get("text", {}).get("body")

            url = f"https://graph.facebook.com/v12.0/{phone_number_id}/messages?access_token={WHATSAPP_TOKEN}"
            data = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "text": {"body": "Ack: " + msg_body}
            }
            headers = {"Content-Type": "application/json"}

            requests.post(url, json=data, headers=headers)

            return {"status": "success"}
        else:
            raise HTTPException(status_code=404, detail="Not Found")
    else:
        raise HTTPException(status_code=404, detail="Not Found")


@app.get("/webhook/")
def verify_webhook(mode: str, token: str, challenge: str):
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return {"challenge": challenge}
        else:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
