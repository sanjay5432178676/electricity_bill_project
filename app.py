from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'secret_key_for_session'

# Connect to MongoDB using environment variable
client = MongoClient(os.environ[mongodb+srv://sanjay:<db_password>@cluster0.rcubvnv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0])
db = client['electricity_db']
users = db['users']
bills = db['bills']

# -------------------- Home (Login) --------------------
@app.route('/')
def login():
    return render_template("login.html")

# -------------------- Register --------------------
@app.route('/register')
def register():
    return render_template("register.html")

@app.route('/register_user', methods=['POST'])
def register_user():
    username = request.form['username']
    password = request.form['password']
    if users.find_one({'username': username}):
        return render_template("error.html", message="Username already exists.")
    users.insert_one({'username': username, 'password': password})
    return redirect('/')

# -------------------- Login --------------------
@app.route('/login_user', methods=['POST'])
def login_user():
    username = request.form['username']
    password = request.form['password']
    user = users.find_one({'username': username, 'password': password})
    if user:
        session['username'] = username
        return redirect('/dashboard')
    return render_template("error.html", message="Invalid login credentials.")

# -------------------- Dashboard --------------------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/')
    return render_template("dashboard.html", user=session['username'])

# -------------------- Bill Generation --------------------
@app.route('/generate_bill')
def generate_bill():
    if 'username' not in session:
        return redirect('/')
    return render_template("generate_bill.html")

@app.route('/calculate_bill', methods=['POST'])
def calculate_bill():
    if 'username' not in session:
        return redirect('/')

    consumer = request.form['consumer']
    meter = request.form['meter']
    conn_type = request.form['type']
    units = int(request.form['units'])
    amount = calculate_amount(units, conn_type)

    bill = {
        'username': session['username'],
        'consumer': consumer,
        'meter': meter,
        'type': conn_type,
        'units': units,
        'amount': amount,
        'status': 'Not Paid',
        'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    bills.insert_one(bill)
    return render_template("bill_result.html", bill=bill)

# -------------------- Bill History --------------------
@app.route('/bill_history')
def bill_history():
    if 'username' not in session:
        return redirect('/')

    filter_status = request.args.get('filter', 'All')
    query = {'username': session['username']}
    if filter_status != 'All':
        query['status'] = filter_status

    all_bills = list(bills.find(query))
    total_unpaid = sum(b['amount'] for b in all_bills if b['status'] == 'Not Paid')
    return render_template("bill_history.html", bills=all_bills, total_unpaid=total_unpaid)

# -------------------- Pay Bill --------------------
@app.route('/pay/<meter>')
def pay_bill(meter):
    bills.update_one({'meter': meter, 'username': session['username']}, {'$set': {'status': 'Paid'}})
    return redirect('/bill_history')

# -------------------- Delete Bill --------------------
@app.route('/delete/<meter>')
def delete_bill(meter):
    bills.delete_one({'meter': meter, 'username': session['username']})
    return redirect('/bill_history')

# -------------------- Search by Meter --------------------
@app.route('/search_meter', methods=['GET', 'POST'])
def search_meter():
    found_bill = None
    if request.method == 'POST':
        meter = request.form['meter']
        found_bill = bills.find_one({'meter': meter})
    return render_template("search_meter.html", bill=found_bill)

# -------------------- Logout --------------------
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# -------------------- Error Page --------------------
@app.route('/error')
def error_page():
    return render_template("error.html", message="Page not found")

# -------------------- Bill Calculation Logic --------------------
def calculate_amount(units, conn_type):
    if conn_type == "domestic":
        if units <= 100:
            return 0
        elif units <= 200:
            return (units - 100) * 2.35
        elif units <= 400:
            return 100 * 2.35 + (units - 200) * 4.70
        elif units <= 500:
            return 100 * 2.35 + 200 * 4.70 + (units - 400) * 6.30
        elif units <= 600:
            return 100 * 2.35 + 200 * 4.70 + 100 * 6.30 + (units - 500) * 8.40
        elif units <= 800:
            return 100 * 2.35 + 200 * 4.70 + 100 * 6.30 + 100 * 8.40 + (units - 600) * 9.45
        elif units <= 1000:
            return 100 * 2.35 + 200 * 4.70 + 100 * 6.30 + 100 * 8.40 + 200 * 9.45 + (units - 800) * 10.50
        else:
            return 100 * 2.35 + 200 * 4.70 + 100 * 6.30 + 100 * 8.40 + 200 * 9.45 + 200 * 10.50 + (units - 1000) * 11.55
    else:
        if units <= 100:
            return units * 6.00
        elif units <= 500:
            return 100 * 6.00 + (units - 100) * 7.00
        else:
            return 100 * 6.00 + 400 * 7.00 + (units - 500) * 8.00

# -------------------- Run App --------------------
if __name__ == "__main__":
    app.run(debug=True)
