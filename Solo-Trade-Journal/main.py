from flask import Flask, render_template, request, url_for, redirect, session, jsonify
from forms import LoginForm, SignUpForm
from flask_sqlalchemy import SQLAlchemy
from requests_toolbelt.utils import dump
from datetime import datetime
from dateutil import tz
import base64
import requests
import pprint
import json



# App Initialisation
app = Flask(__name__)
app.config['SECRET_KEY'] = "secret_key"

# DB Initialisation
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///User.db"
db.init_app(app)


# Defining the table(s)
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, unique=False, nullable=False)


class TradingAccounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    account_login = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    broker = db.Column(db.String, nullable=False)
    broker_server = db.Column(db.String, nullable=False)
    mt_version = db.Column(db.Integer, nullable=False)

    # Relationship between tables
    user = db.relationship('Users', backref=db.backref('trading_accounts', lazy=True))


with app.app_context():
    db.create_all()

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


# DUMPING REQUESTS
def dump_requests(response):
    data = dump.dump_all(response)
    print(data.decode('utf-8'))


def calcRiskReward(open_price, stop_loss, take_profit):
    risk = open_price - stop_loss
    reward = take_profit - open_price
    risk_reward_ratio = reward / risk
    return round(risk_reward_ratio, 2)


def convertToDay(date_str):
    # Parse the datetime string into a datetime object
    date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
    # Get the day of the week (e.g., 'Monday')
    day_of_week = date_obj.strftime('%A')
    return day_of_week

def convertToTime(date_str):
    # Parse the datetime string into a datetime object
    date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
    # Get the time of the day (e.g., '12:00')
    time_of_day = date_obj.strftime('%H:%M')
    return time_of_day


# VIEWS
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    page_title = "Log-In"

    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = Users.query.filter_by(email=email).first()

        if user:
            if user.password == password:
                session['user_id'] = user.id
                return redirect('/accounts')
            else:
                error_message = "Incorrect password. Please try again."
                return render_template('login.html', page_title=page_title, error_message=error_message)
        else:
            error_message = "No user found with that email. Please sign up first."
            return render_template('login.html', page_title=page_title, error_message=error_message)

    return render_template('login.html', page_title=page_title)


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    page_title = "Sign-Up"

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Adding User to the table
        user = Users(
            name=name,
            email=email,
            password=password
        )

        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('signup.html', page_title=page_title)


@app.route('/accounts', methods=['POST', 'GET'])
def accounts():
    # If user isn't logged in direct to login page
    if 'user_id' not in session:
        return redirect('/login')
    else:
        if request.method == "POST":
            name = request.form['name']
            account_number = request.form['account-login']
            broker = request.form['broker']
            password = request.form['password']
            mt_version = request.form['mt-version']
            server = request.form['server']

            print(name)
            print(account_number)
            print(password)
            print(mt_version)
            print(server)

            # Getting Broker Server ID
            endpoint = "broker-servers"
            url = base_url + endpoint
            print(f"URL is: {url}")
            data = {
                "name": server,
                "mt_version": mt_version
            }
            response = requests.get(url, headers=header, json=data)
            data = response.json()
            print(f"Data is: {data}")

            # Filtering through all broker servers
            filtered_content = [broker_id for broker_id in data['data'] if broker_id['name'] == server]
            print(f"Filtered Content: {filtered_content}")
            id_value = filtered_content[0]['id']
            print(f"ID Value is: {id_value}")

            # Sending info to create account endpoint
            endpoint = "accounts"
            url = base_url + endpoint
            print(f"URL is: {url}")

            data = {
                "account_name": name,
                "mt_version": mt_version,
                "account_number": account_number,
                "password": password,
                "broker_server_id": id_value
            }

            response = requests.post(url, headers=header, json=data)
            data = response.json()
            print(f"Data is: {data}")
            print(f"Status Code:", response.status_code)

            if response.status_code == 200:
                newTradingAccount = TradingAccounts(
                    user_id=session['user_id'],
                    name=name,
                    account_login=account_number,
                    password=password,
                    broker=broker,
                    broker_server=server,
                    mt_version=mt_version
                )

                db.session.add(newTradingAccount)
                db.session.commit()
                # Return user to the page with the account table

                user_id = session['user_id']
                user_accounts = TradingAccounts.query.filter_by(user_id=user_id).all()
                print("User accounts:")
                for account in user_accounts:
                    print(account.name)

                return render_template('accounts.html', user_accounts=user_accounts)

            else:
                error_message = "Try again"
                return error_message

        user_id = session['user_id']
        user_accounts = TradingAccounts.query.filter_by(user_id=user_id).all()
        return render_template('accounts.html', user_accounts=user_accounts)


@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    else:
        user_id = session['user_id']

        # Grabbing the account ID from the link the user pressed from the account table
        account_id1 = int(request.args.get('account_id'))

        # Getting all accounts
        endpoint = "accounts"
        url = base_url + endpoint
        print(f"URL: {url}")
        response = requests.get(url, headers=header)
        data = response.json()
        print(data)

        # Filtering through the DB

        account = TradingAccounts.query.filter_by(id=account_id1, user_id=session['user_id']).first()
        print(f"Account: {account}")
        accountLogin = account.account_login
        print(f"Login: {accountLogin}")

        data = {
            "account_number": accountLogin
        }

        response = requests.get(url, headers=header, json=data)
        data = response.json()
        print(f"Response Data:{data}") # prints the json

        allAccData = data['data']
        print(f"All Acc Data:")
        pp = pprint.PrettyPrinter(width=41, compact=True)
        pp.pprint(data)

        new_data = data['data']
        print(f"New Data:")
        pp = pprint.PrettyPrinter(width=41, compact=True)
        pp.pprint(new_data)

        # Account Name
        account_name = account.name
        print(f"Account Name: {account_name}")

        for entry in new_data:
            account_name = entry.get('account_name')  # Get the value associated with the key 'account_name'
            if account_name == account.name:  # Check if 'account_name' matches the name of the account object
                print(f"Entry is: {entry}")

        acc_id = entry['id']
        print(f"ID: {acc_id}")

        weekly_profit = entry['weekly_profit']
        print("Weekly Profit:", weekly_profit)

        account_balance = entry['balance']
        print("Balance:", account_balance)

        total_profit = entry['total_profit']


        endpoint = f"analyses"
        url = base_url + endpoint
        response = requests.get(url, headers=header)
        data = response.json()
        print(data)


        entry = data.get('data')
        print("Entry:",entry)
        account_size = entry[0]['total_deposits']
        print("total deposits", account_size)

        # broker = new_data[0]['broker']
        #print("Broker:", broker)

        platform = new_data[0]['mt_version']



                        # All of the user's trades
        endpoint = f"trades"
        url = base_url + endpoint
        response = requests.get(url, headers=header)
        data = response.json()
        pp = pprint.PrettyPrinter(width=41, compact=True)
        print("Trades")
        pp.pprint(data)

        trades_data = data['data']

                    # List to store trade dictionaries
        trades_list = []

        # Iterating over trades data and extracting required information
        for trade in trades_data:
            # Ignoring deposit transactions
            if trade['type'] != 'deposit':

                trade_info = {
                    'open_time': trade['open_time'],
                    'symbol': trade['symbol'],
                    'lots': trade['lots'],
                    'type': trade['type'],
                    'rr': calcRiskReward(trade['open_price'], trade['stop_loss'], trade['take_profit'])
                }
                trades_list.append(trade_info)

        # Printing the list of trade dictionaries
        #print("Trades",trades_list)
        pp = pprint.PrettyPrinter(width=41,compact=True)
        pp.pprint(trades_list)


        # Monthly Analysis
        endpoint = f"analyses/{acc_id}/monthlies"
        url = base_url + endpoint
        response = requests.get(url, headers=header)
        data = response.json()
        print("Monthly data")
        pp = pprint.PrettyPrinter(width=41, compact=True)
        pp.pprint(data)



        # Iterating over data and extracting required information
        monthly_list = []
        for entry in data['data']:
            time_string = entry['date']
            dt = datetime.strptime(time_string, "%Y-%m-%d")
            dt = dt.replace(tzinfo=tz.gettz('UTC'))
            unix_timestamp = dt.timestamp()

            data_info = {
                'date': unix_timestamp,
                'growth': entry['growth'],
            }
            monthly_list.append(data_info)

        # Printing the list of data dictionaries
        print("Data list:", monthly_list)
        monthly_list_json = json.dumps(monthly_list)
        # Writing the data to a JSON file
        with open('monthly_data.json', 'w') as f:
            f.write(monthly_list_json)





        # filtered_content = [broker_id for broker_id in data['data'] if broker_id['name'] == server]

    return render_template('dashboard.html', weekly_profit=weekly_profit,
                           account_balance=account_balance, total_profit=total_profit,
                           account_size=account_size, platform=platform,
                           trades_list=trades_list, monthly_list=monthly_list)



@app.route('/delete_account/<account_id>', methods=['DELETE'])
def delete_account(account_id):
    try:
        # Get the account
        account = TradingAccounts.query.get(account_id)
        if account:
            # Delete the account
            db.session.delete(account)
            db.session.commit()
            return jsonify(success=True)
        else:
            return jsonify(success=False, error='Account not found.')
    except Exception as e:
        return jsonify(success=False, error=str(e))



@app.route('/copy-trading', methods=['POST', 'GET'])
def copytrading():
    error_message = None
    master_account = None
    slave_account = None

    if request.method == "POST":
        trading_accounts = TradingAccounts.query.filter_by(user_id=session['user_id']).all()

        master_account = request.form['master-account']
        slave_account = request.form['slave-account']
        risk_type = request.form['risk-type']
        risk_value = request.form['risk-value']

        if master_account == slave_account:
            error_message = "Can't be the same account"
            return render_template('copy_trading.html',
                                   error_message=error_message, master_account=master_account,
                                   slave_account=slave_account, trading_accounts=trading_accounts)

        # Creating the copier
        endpoint = "copiers"
        url = base_url + endpoint
        body = {
            "lead_id": master_account,
            "follower_id": slave_account,
            "risk_type": risk_type,
            "risk_value": risk_value,
        }
        response = requests.post(url, headers=header, json=body)
        data = response.json()
        print("Data: \n", data)

        return redirect('/dashboard')


    trading_accounts = TradingAccounts.query.filter_by(user_id=session['user_id']).all()
    return render_template('copy_trading.html', trading_accounts=trading_accounts,
                           error_message=error_message, master_account=master_account,
                           slave_account=slave_account)

"""
@app.route('/submit-copy', methods=['POST', 'GET'])
def submitCopy():
    masteraccount = request.form['master-account']
    print(masteraccount)
    slaveaccount = request.form['slave-account']
    print(slaveaccount)
    return render_template('dashboard.html')
"""


@app.route('/analysis')
def analysis():
                # All of the user's trades
    endpoint = f"trades"
    url = base_url + endpoint
    response = requests.get(url, headers=header)
    data = response.json()
    pp = pprint.PrettyPrinter(width=41, compact=True)
    print("Trades")
    pp.pprint(data)

    trades_data = data['data']


    trades_list = []

                # Iterating over trades data and extracting required information
    for trade in trades_data:
        # Ignoring deposit transactions
        if trade['type'] != 'deposit':
            trade_info = {
                'day': convertToDay(trade['open_time']),
                'open_time': convertToTime(trade['open_time']),
                'symbol': trade['symbol'],
                'lots': trade['lots'],
                'type': trade['type'],
                'rr': calcRiskReward(trade['open_price'], trade['stop_loss'], trade['take_profit']),
                'profit': trade['profit'],
                'tags': None
            }
            trades_list.append(trade_info)

    return render_template('analysis.html', trades_list=trades_list)


if __name__ == '__main__':
    app.run(debug=True)
