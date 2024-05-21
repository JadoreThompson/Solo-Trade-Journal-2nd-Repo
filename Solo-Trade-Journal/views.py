from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import base64
import requests
from models import Users, TradingAccounts, CopyTrading, db

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
    error = None
    page_title = "Signup"

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        password = generate_password_hash(password)
        print(name, email, password)

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
            response = requests.get(url, headers=header)
            data = response.json()
            data = data['data']
            print("Broker Servers: ", data)

            found = False
            for item in data:
                if item['mt_version'] == mt_version and item['name'] == broker_server:
                    found = True
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
    if found:

        #   Sending variables to the dashboard
        print("Account found: ", found_item)
        weekly_profit = found_item['weekly_profit']
        account_balance = found_item['balance']
        total_profit = found_item['total_profit']

        trades_list = {
        }




    return render_template("dashboard.html")


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