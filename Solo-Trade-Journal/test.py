from pprint import pprint
import base64
import requests
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


# endpoint = "analyses/1071483"
# endpoint = "events/accounts"

from datetime import timezone

current_date = datetime.now(timezone.utc)
one_week_ago = current_date - timedelta(days=7)
print(current_date)

# Getting all trades
endpoint = "trades"
url = base_url + endpoint
response = requests.get(url, headers=header)
data = response.json()
pprint(data)

last_weeks_trades = []
last_weeks_profit = 0
for trade in data['data']:
    parsed_datetime = parser.isoparse(trade['open_time'])
    if parsed_datetime > one_week_ago:
        last_weeks_trades.append(trade)
        print(last_weeks_trades)
        for trade in last_weeks_trades:
            last_weeks_profit += trade['profit']

print("last weejks prof", last_weeks_profit)



