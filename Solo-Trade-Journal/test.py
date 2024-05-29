from pprint import pprint
import base64
import requests
import math
from datetime import datetime, timedelta, timezone
from dateutil import parser

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


# Getting monthly growth to pass into dashboard chart

tradesync_account_id = 1071850

endpoint = f"analyses/{tradesync_account_id}/monthlies"
url = base_url + endpoint

response = requests.get(url, headers=header)
data = response.json()
pprint(data)








