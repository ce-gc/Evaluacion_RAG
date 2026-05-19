import requests
import concurrent.futures
import pytest

BASE_URL = "http://127.0.0.1:8000"


def _call(path: str, method: str = "get", json=None):
    url = BASE_URL + path
    try:
        if method == "get":
            return requests.get(url, timeout=5)
        else:
            return requests.post(url, json=json, timeout=5)
    except requests.exceptions.RequestException:
        pytest.skip(f"Server not available at {BASE_URL}")


def test_hola_mundo():
    r = _call("/hola_mundo")
    assert r.status_code == 200


@pytest.mark.parametrize("payload", [
    {"input": "", "model": "stub"},
    {"input": "¡Hola! 🌟 ¿Cómo estás? 你好 123 @#$%", "model": "stub"},
    {"input": "Esta es una frase repetida. " * 100, "model": "stub"},
    {"input": "Test model fallback", "model": "modelo-fantasma"},
])
def test_predict(payload):
    r = _call("/predict", method="post", json=payload)
    assert r.status_code in (200, 422)


def test_concurrency():
    # small concurrency smoke test — skips if server unavailable
    payloads = [{"input": f"Request {i}", "model": "stub"} for i in range(5)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(requests.post, f"{BASE_URL}/predict", json=p, timeout=5) for p in payloads]
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                r = future.result()
                results.append(r.status_code)
            except requests.exceptions.RequestException:
                pytest.skip("Server not available during concurrency test")
    assert all(s in (200, 422) for s in results)
