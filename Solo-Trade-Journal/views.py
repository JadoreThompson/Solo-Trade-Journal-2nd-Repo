from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import base64
import requests
from models import Users, TradingAccounts, CopyTrading, db
from datetime import datetime, timedelta, timezone
from dateutil import parser
import math
import pprint
import json
from dotenv import load_dotenv
import os

#   Creating a blueprint ( area for all the routes )
views = Blueprint("views", __name__)

# TradeSync API
base_url = "https://api.tradesync.io/"

load_dotenv('.env')
apikey: str = os.getenv('API_KEY')
secretkey: str = os.getenv('SECRET_KEY')

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

    def get_brokers():
        endpoint = "brokers"
        url = base_url + endpoint
        response = requests.get(url, headers=header)
        data = response.json()
        data = data['data']

        all_brokers = []
        for broker in data:
            all_brokers.append(broker)
        return all_brokers
    def get_broker_servers():
        endpoint = "broker-servers"
        url = base_url + endpoint
        response = requests.get(url, headers=header)
        data = response.json()
        data = data['data']

        all_broker_servers = []
        for broker_server in data:
            all_broker_servers.append(broker_server)

        return all_broker_servers

    if request.method == "POST":

        trading_name = request.form.get("name")
        trading_number = request.form.get("account-login")
        trading_password = request.form.get("password")
        mt_version = request.form.get("mt-version")
        trading_broker = request.form.get("broker")
        trading_server = request.form.get("broker-server")

        """
        print("Trading Name: ", trading_name)
        print("Trading Number: ", trading_number)
        print("Trading Password: ", trading_password)
        print("MT Version: ", mt_version)
        print("Trading Broker: ", trading_broker)
        print("Trading Server: ", trading_server)
        """

        def create_account():
            endpoint = "accounts"
            url = base_url + endpoint
            data = {
                "account_name": trading_name,
                "account_number": trading_number,
                "password": trading_password,
                "mt_version": mt_version,
                "broker_id": trading_broker,
                "broker_server_id": trading_server
            }
            response = requests.post(url, headers=header, json=data)
            print("Response: ", response.json())
            return response.json()

        data = create_account()
        if data['status'] == 200:
            new_account = TradingAccounts(user_id=session['user_id'], name=trading_name,
                                          account_number=trading_number)
            db.session.add(new_account)
            db.session.commit()

            return redirect(url_for("views.accounts"))


    accounts = TradingAccounts.query.filter_by(user_id=session['user_id']).all()
    return render_template("accounts.html", all_brokers=get_brokers(),
                           all_servers=get_broker_servers(), accounts=accounts)



@views.route("/dashboard/<int:account_id>")
def dashboard(account_id):

    def get_trading_account_id(account_id):
        session['account_id'] = account_id
        account = TradingAccounts.query.filter_by(id=account_id).first()
        return account.account_number

    def get_acc_pnl(tradesync_acc_id):
        print("TradeSync Account ID: ", tradesync_acc_id)

        endpoint = "accounts"
        url = base_url + endpoint
        response = requests.get(url, headers=header)
        data = response.json()
        data = data['data']
        print("Account Data: ", data)

        for account in data:
            if account['account_number'] == tradesync_acc_id:
                return account

    def get_trades(tradesync_account_id):
        endpoint = "accounts"
        url = base_url + endpoint
        response = requests.get(url, headers=header)
        data = response.json()
        data = data['data']

        for account in data:
            if account['account_number'] == tradesync_account_id:
                ts_account = account

        ts_account_id = ts_account['id']
        session['tradesync_acc_id'] = ts_account_id

        endpoint = "trades"
        url = base_url + endpoint
        response = requests.get(url, headers=header)
        data = response.json()
        data = data['data']

        trades_list = []
        for trade in data:
            if trade['account_id'] == ts_account_id:
                trades_list.append(trade)

        return trades_list

    def get_monthly_growth(tradesync_account_id):
        endpoint = f"analyses/{tradesync_account_id}/monthlies"
        url = base_url + endpoint
        response = requests.get(url, headers=header)
        data = response.json()
        return data['data']



    tradesync_account_id = int(get_trading_account_id(account_id))
    session['tradesync_acc_number'] = tradesync_account_id

    # Top row variables
    acc_dict = get_acc_pnl(tradesync_account_id)
    weekly_profit = acc_dict['weekly_profit']
    monthly_profit = acc_dict['monthly_profit']
    balance = acc_dict['equity']

    # Chart data
    monthly_growth = get_monthly_growth(session['tradesync_acc_id'])
    json_data = json.dumps(monthly_growth)

    # Trades Table
    trades_list = get_trades(tradesync_account_id)
    session['trades_list'] = trades_list



    return render_template("dashboard.html", weekly_profit=weekly_profit, monthly_profit=monthly_profit
                           , balance=balance, trades_list=trades_list, json_data=json_data)


@views.route("/dashboard/<int:account_id>/analysis")
def analysis(account_id):

    account_id = session['account_id']
    def get_trading_account_id(account_id):
        session['account_id'] = account_id
        account = TradingAccounts.query.filter_by(id=account_id).first()
        return account.account_number

    def get_trades(tradesync_account_id):
        endpoint = "accounts"
        url = base_url + endpoint
        response = requests.get(url, headers=header)
        data = response.json()
        data = data['data']

        for account in data:
            if account['account_number'] == tradesync_account_id:
                ts_account = account

        ts_account_id = ts_account['id']
        session['tradesync_acc_id'] = ts_account_id

        endpoint = "trades"
        url = base_url + endpoint
        response = requests.get(url, headers=header)
        data = response.json()
        data = data['data']

        trades_list = []
        for trade in data:
            if trade['account_id'] == ts_account_id:
                trades_list.append(trade)

        return trades_list


    tradesync_account_id = int(get_trading_account_id(account_id))
    trades_list = get_trades(session['tradesync_acc_number'])
    print("Trades List: ", trades_list)

    return render_template("analysis.html")


@views.route("/copytrading")
def copytrading():
    return render_template("copytrading.html")

@views.route("/delete-account/<int:account_id>")
def delete_account(account_id):
    account = TradingAccounts.query.filter_by(id=account_id).first()
    db.session.delete(account)
    db.session.commit()

    account_id = session['tradesync_acc_id']

    endpoint = f"accounts/{account_id}"
    url = base_url + endpoint
    response = requests.delete(url, headers=header)
    print("Delete Response:", response.json())

    return redirect(url_for("views.accounts"))