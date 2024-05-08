from flask import Flask, render_template, request, url_for, redirect, session
from forms import LoginForm, SignUpForm
from flask_sqlalchemy import SQLAlchemy
import base64
import requests
import pprint
from requests_toolbelt.utils import dump

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

# VIEWS
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    page_title = "Log-In"

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
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
                error_messgae = "Try again"
                return error_messgae

        user_id = session['user_id']
        user_accounts = TradingAccounts.query.filter_by(user_id=user_id).all()
        return render_template('accounts.html', user_accounts=user_accounts)


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    else:
        user_id = ['user_id']

        # Grabbing the account ID from the link the user pressed from the account table
        account_id0 = request.args.get('account_id')
        print(account_id0)  # Printing it to the console

        # Getting all accounts
        endpoint = "accounts"
        url = base_url + endpoint
        print(f"URL: {url}")
        response = requests.get(url, headers=header)
        data = response.json()
        print(data)

        # Filtering through the DB

        account = TradingAccounts.query.filter_by(id=account_id0, user_id=session['user_id']).first()
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
                print(entry)

        acc_id = entry['id']
        print(f"ID: {acc_id}")

        endpoint = f"/analyses/{acc_id}/days"
        url = base_url + endpoint

        response = requests.get(url, headers=header)
        dump_requests(response)

        data = response.json()
        print(data)

        # filtered_content = [broker_id for broker_id in data['data'] if broker_id['name'] == server]

    return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(debug=True)
