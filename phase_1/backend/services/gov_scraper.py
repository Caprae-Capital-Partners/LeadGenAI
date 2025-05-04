import requests

HF_TOKEN = "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"
url = "https://fatmagician-gov-leads.hf.space/search"  # ✅ CORRECT URL

headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

data = {
    "location": "California",
    "category": "barbershop"
}

response = requests.post(url, json=data, headers=headers)

print(response.status_code)
try:
    print(response.json())
except requests.exceptions.JSONDecodeError:
    print("Non-JSON response:", response.text)

