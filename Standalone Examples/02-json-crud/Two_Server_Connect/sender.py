import time, requests

URL = "http://127.0.0.1:8000/ask"

HEADERS = {"X-API-Key": "supersecret"}

payload = {"user_id": 42, "question": "Hello How are you?"}

for attempt in range(3):  # simple retry
    try:
        r = requests.post(URL, json=payload, headers=HEADERS, timeout=(3, 10))
        r.raise_for_status()
        print(r.json())     # {'status':'ok','reply':'...'}
        break
    except requests.RequestException as e:
        if attempt == 2: raise
        time.sleep(1.5)
