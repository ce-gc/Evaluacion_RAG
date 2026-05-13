import requests
import time
import concurrent.futures

BASE_URL = "http://127.0.0.1:8000"

def test_hola_mundo():
    print("Testing /hola_mundo...")
    try:
        r = requests.get(f"{BASE_URL}/hola_mundo")
        print(f"Status: {r.status_code}, Response: {r.json()}")
    except Exception as e:
        print(f"Error connecting to server: {e}")

def test_predict(payload):
    print(f"Testing /predict with model: {payload.get('model')}")
    try:
        r = requests.post(f"{BASE_URL}/predict", json=payload)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Response Meta: {r.json().get('meta')}")
        else:
            print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

def run_all_tests():
    print("--- INICIANDO TESTS EXTRA ---")
    
    # 1. Test Hola Mundo
    test_hola_mundo()
    print("-" * 30)

    # 2. Caso Límite: Input vacío (Debe dar 422)
    test_predict({"input": "", "model": "stub"})
    print("-" * 30)

    # 3. Caso Límite: Caracteres especiales
    test_predict({"input": "¡Hola! 🌟 ¿Cómo estás? 你好 123 @#$%", "model": "stub"})
    print("-" * 30)

    # 4. Caso Límite: Input muy largo
    long_input = "Esta es una frase repetida. " * 100
    test_predict({"input": long_input, "model": "stub"})
    print("-" * 30)

    # 5. Caso Límite: Modelo inexistente (Cae en el else -> stub)
    test_predict({"input": "Test model fallback", "model": "modelo-fantasma"})
    print("-" * 30)

    # 6. Test de concurrencia (Simulando 5 peticiones rápidas)
    print("Testing concurrency (5 requests)...")
    payloads = [{"input": f"Request {i}", "model": "stub"} for i in range(5)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(requests.post, f"{BASE_URL}/predict", json=p) for p in payloads]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            r = future.result()
            print(f"Request {i} completed with status {r.status_code}")

if __name__ == "__main__":
    run_all_tests()
