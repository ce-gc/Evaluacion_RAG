# server.py
from fastapi import FastAPI
from pydantic import BaseModel, Field
import time

from engine_gemma import predict as stub_predict
from engine_gemma2 import predict as gemma2_predict

app = FastAPI()

class PredictIn(BaseModel):
    input: str = Field(..., min_length=1)
    model: str = "stub"

@app.post("/predict")
def predict(body: PredictIn):
    t0 = time.time()

    if body.model == "gemma2-2b":
        output_text = gemma2_predict(body.input)
        provider = "gemma2-2b"
    else:
        output_text = stub_predict(body.input)
        provider = "stub"

    ms = int((time.time() - t0) * 1000)
    return {
        "output": output_text,
        "meta": {
            "provider": provider,
            "latency_ms": ms,
            "input_chars": len(body.input),
            "output_chars": len(output_text),
            "timestamp": time.time()
        }
    }

@app.get("/hola_mundo")
def hola_mundo():
    return {"mensaje": "¡Hola, mundo!", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)