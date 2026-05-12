import requests

GHOST_URL = "http://localhost:2368"
headers = {
    "X-Ghost-Version": "5.0",
    "Origin": GHOST_URL,
    "Referer": f"{GHOST_URL}/ghost/",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

endpoints = [
    "/ghost/api/admin/setup/",
    "/ghost/api/v4/admin/setup/",
    "/ghost/api/v5/admin/setup/",
    "/ghost/api/setup/"
]

for ep in endpoints:
    url = f"{GHOST_URL}{ep}"
    print(f"GET {url}")
    try:
        resp = requests.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

    print(f"\nPOST {url}")
    try:
        resp = requests.post(url, headers=headers, json={"setup": [{"name": "test", "email": "test@example.com", "password": "password123", "blogTitle": "test"}]})
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 40)
