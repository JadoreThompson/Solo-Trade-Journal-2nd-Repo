from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import base64
import requests
from models import Users, TradingAccounts, CopyTrading, db
from datetime import datetime, timedelta, timezone
from dateutil import parser

#   Creating a blueprint ( area for all the routes )
views = Blueprint("views", __name__)

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

@views.route("/")
def index():
    return render_template("index.html")


@views.route("/signup", methods=["POST", "GET"])
def signup():
    minCharacters = 8
    error = None
    page_title = "Signup"

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        password = generate_password_hash(password)
        print(name, email, password)

        if len(password) < minCharacters :
            error_message = "More characters"
            return render_template('signup.html', page_title=page_title, error_message=error_message)

        #   Add user to database
        new_user = Users(name=name, email=email, password=password)
        print(new_user)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("views.login"))

    return render_template("signup.html", page_title=page_title)



@views.route("/login", methods=["POST", "GET"])
def login():
    page_title = "Login"
    error = None

    # Checking if user exists
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        print("User Credentials: ", email, password)

        #   Check if user exists
        user = Users.query.filter_by(email=email).first()
        print("User:", user)
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for("views.accounts"))
        else:
            error = "Invalid email or password"
            return render_template("login.html", page_title=page_title, error=error)


    return render_template("login.html", page_title=page_title)


@views.route("/accounts", methods=["POST", "GET"])
def accounts():
    if 'user_id' not in session:
        return redirect(url_for("views.login"))
    else:
        u = session['user_id']
        print("User ID: ", u)
        if request.method == "POST":

            #   Grabbing account credentials
            name = request.form.get("name")
            account_login = request.form.get("account-login")
            password = request.form.get("password")
            broker = request.form.get("broker")
            broker_server = request.form.get("broker-server")
            mt_version = request.form.get("mt-version")
            print("Add account credentials: ", name, account_login, password, broker, broker_server, mt_version)

            #   Getting broker server id for account creation
            endpoint = "broker-servers"
            url = base_url + endpoint
            body = {
                'mt_version': mt_version,
            }
            response = requests.get(url, headers=header, json=body)
            data = response.json()
            data = data['data']
            print("Broker Servers: ", data)

            found = False
            for item in data:
                if item['name'] == broker_server:
                    found = True
                    print("found")
                    found_item = item


            if found:
                broker_server_id = found_item['broker_id']
                print("Broker found", found_item,'\n' "Broker Server ID", broker_server_id)

                #   Add account to database
                endpoint = "accounts"
                url = base_url + endpoint
                body = {
                    "account_name": name,
                    "mt_version": mt_version,
                    "account_number": account_login,
                    "password": password,
                    "broker_server_id": broker_server_id
                }
                response = requests.post(url, headers=header, json=body)
                data = response.json()
                print("Account Creation Response ", data)

                if response.status_code == 200:
                    account = TradingAccounts(name=name, account_login=account_login, password=password, broker=broker, broker_server=broker_server, mt_version=mt_version, user_id=session['user_id'])
                    db.session.add(account)
                    db.session.commit()
                    return redirect(url_for("views.accounts"))
            else:
                error = True
                print("No broker found")
                error_message = "Broker server not found"
                return render_template("accounts.html", error=error, error_message=error_message)


    #   Loading all the user's accounts
    accounts = TradingAccounts.query.filter_by(user_id=session['user_id']).all()
    return render_template("accounts.html", accounts=accounts)

@views.route("/dashboard/<int:account_id>")
def dashboard(account_id):
    session['account_id'] = account_id
    if 'user_id' not in session:
        return redirect(url_for("views.login"))
    if 'account_id' not in session:
        return redirect(url_for("views.accounts"))

    #   Use session id to get account name
    print("Session ID: ", session['account_id'])
    account = TradingAccounts.query.filter_by(user_id=session['user_id'], id=session['account_id']).first()
    print("Account Name: ", account.name)

    #   Using name as the identifier
    endpoint = "accounts"
    url = base_url + endpoint
    response = requests.get(url, headers=header)
    data = response.json()
    print(data)

    data = data['data']
    found = False
    for item in data:
        if item['account_name'] == account.name:
            found = True
            found_item = item
            print("Account found", found_item)

    tradesync_account_id = found_item['id']
    endpoint = f"analyses/{tradesync_account_id}"
    url = base_url + endpoint
    response = requests.get(url, headers=header)
    data = response.json()

    # Working out 7d pnl
    current_date = datetime.now(timezone.utc)
    one_week_ago = current_date - timedelta(days=7)

    # Getting all trades
    endpoint = "trades"
    url = base_url + endpoint
    response = requests.get(url, headers=header)
    data = response.json()

    last_weeks_trades = []
    last_weeks_profit_num = 0
    week_before_last_trades = []
    week_before_last_profit_num = 0
    two_weeks_ago = one_week_ago - timedelta(days=7)

    for trade in data['data']:
        parsed_datetime = parser.isoparse(trade['open_time'])
        if parsed_datetime > one_week_ago:
            last_weeks_trades.append(trade)
            last_weeks_profit_num += trade['profit']
        elif parsed_datetime > two_weeks_ago:
            week_before_last_trades.append(trade)
            week_before_last_profit_num += trade['profit']

    if last_weeks_profit_num < 0:
        last_weeks_profit = f"-${str(last_weeks_profit_num)}"
    else:
        last_weeks_profit = f"+${str(last_weeks_profit_num)}"

    if week_before_last_profit_num < 0:
        week_before_last_profit = f"-${str(week_before_last_profit_num)}"
    else:
        week_before_last_profit = f"+${str(week_before_last_profit_num)}"

    profit_difference = last_weeks_profit_num - week_before_last_profit_num
    if profit_difference < 0:
        profit_difference = f"-${str(profit_difference)}"
    else:
        profit_difference = f"+${str(profit_difference)}"
    # End of getting 7d pnl


    return render_template("dashboard.html", last_weeks_profit=last_weeks_profit, profit_difference=profit_difference)


@views.route("/analysis")
def analysis():
    if 'user_id' not in session:
        return redirect(url_for("views.login"))
    if 'account_id' not in session:
        return redirect(url_for("views.accounts"))

    account = TradingAccounts.query.filter_by(user_id=session['user_id'], id=session['account_id']).first()
    print("Account Name: ", account.name)

    trades_list = {

    }
    return render_template("analysis.html")


@views.route("/copytrading")
def copytrading():
    return render_template("copytrading.html")