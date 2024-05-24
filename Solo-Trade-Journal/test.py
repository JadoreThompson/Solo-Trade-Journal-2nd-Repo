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


password = "dog"
if len(password) > 5:
    print(len(password))
else:
    print("gone")
