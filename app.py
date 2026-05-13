# app.py
import gradio as gr
import requests

API_URL = "http://127.0.0.1:8000/predict"

def call_api(text, model_name):
    payload = {"input": text, "model": model_name}
    # Ampliamos el timeout porque la CPU tarda más de 60 segundos en generar texto
    r = requests.post(API_URL, json=payload, timeout=600)
    
    if r.status_code == 422:
        raise gr.Error("Error 422: El texto de entrada no puede estar vacío.")
    elif not r.ok:
        raise gr.Error(f"Error del servidor: HTTP {r.status_code}")
        
    data = r.json()
    return data["output"], data["meta"]

demo = gr.Interface(
    fn=call_api,
    inputs=[
        gr.Textbox(label="Input"),
        gr.Dropdown(choices=["stub", "gemma2-2b"], value="stub", label="Modelo")
    ],
    outputs=[gr.Textbox(label="Output"), gr.JSON(label="Meta")],
    title="Cliente de /predict",
)

if __name__ == "__main__":
    demo.launch()
