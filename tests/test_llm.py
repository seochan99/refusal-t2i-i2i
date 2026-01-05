import requests
import os

api_key = "AIzaSyAydyQUI9vZAwqy6CZHI2ZdtNoHBLym40M"
url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

payload = {
    "model": "gemini-3-flash-preview",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, are you Gemini 3 Flash?"}
    ],
    "max_tokens": 100
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

print(f"Testing URL: {url}")
try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
