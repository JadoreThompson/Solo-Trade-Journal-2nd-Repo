import base64
import requests

# TradeSync API
base_url = "https://api.tradesync.io/"

apikey = 'kcsiJZvwfGX81Rw9op2a'
secretkey = 'RjvCNYNjrsiwwUvkFBXG'
credentials = f"{apikey}:{secretkey}"

encoded = base64.b64encode(credentials.encode()).decode()

header = {
    "Authorization": f"Basic {encoded}",
    "Content-Type": 'application/json'  # Fixed typo here
}


endpoint = "analyses/1069986"
url = base_url + endpoint
response = requests.get(url, headers=header)
print(response.json())
