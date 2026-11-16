import requests

try:
    r = requests.get("http://127.0.0.1:27080/radar/state", timeout=1)
    print("Response from 27080:", r.status_code, r.text[:100])
except Exception as e:
    print("Error contacting 27080:", e)
