# server.py
from fastapi import FastAPI
from pydantic import BaseModel, Field
import time

from engine_gemma import predict as stub_predict
try:
    from engine_gemma2 import predict as gemma2_predict
except Exception:
    gemma2_predict = None

# RAG support (optional)
try:
    from rag.retriever import build_index, retrieve_topk, build_rag_prompt
    _RAG_INDEX = build_index("docs") if __name__ == "__main__" or True else None
except Exception:
    build_index = None
    retrieve_topk = None
    build_rag_prompt = None
    _RAG_INDEX = None
    
from validator import validate_output, repair_prompt

app = FastAPI()

class PredictIn(BaseModel):
    input: str = Field(..., min_length=1)
    model: str = "stub"
    use_rag: bool = False

@app.post("/predict")
def predict(body: PredictIn):
    t0 = time.time()

    # If RAG requested and index available, prepend context
    prompt_input = body.input
    if getattr(body, "use_rag", False) and _RAG_INDEX is not None and retrieve_topk is not None:
        retrieved = retrieve_topk(_RAG_INDEX, body.input, k=3)
        chunks = [c for c, s in retrieved]
        prompt_input = build_rag_prompt(chunks, body.input)

    if body.model == "gemma2-2b" and gemma2_predict is not None:
        output_text = gemma2_predict(prompt_input)
        provider = "gemma2-2b"
    else:
        output_text = stub_predict(prompt_input)
        provider = "stub"

    # Validate model output and attempt one-shot repair if JSON parse fails
    try:
        ok, err_type, parsed = validate_output(output_text)
    except Exception:
        ok = False
        err_type = "validation_error"
        parsed = None

    repaired = False
    if not ok and err_type == "json_parse_error":
        rp = repair_prompt(output_text)
        try:
            # use same provider to repair
            if provider == "gemma2-2b" and gemma2_predict is not None:
                repaired_raw = gemma2_predict(rp)
            else:
                repaired_raw = stub_predict(rp)
            ok2, err2, parsed2 = validate_output(repaired_raw)
            if ok2:
                output_text = repaired_raw
                repaired = True
                parsed = parsed2
                err_type = None
        except Exception:
            pass

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