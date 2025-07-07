from flask import Flask, render_template, request, redirect, session, url_for
import os
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USERS_FILE = 'users.txt'
BILLS_FILE = 'bills.txt'

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/register_user', methods=['POST'])
def register_user():
    username = request.form['username']
    password = request.form['password']
    
    with open('users.txt', 'a') as f:
        f.write(f"{username}|{password}\n")
    
    return redirect('/')


@app.route('/login', methods=['GET'])
def login_user():
    username = request.args.get('username')
    password = request.args.get('password')

    with open(USERS_FILE, 'r') as f:
        for line in f:
            user, pwd = line.strip().split('|')
            if username == user and password == pwd:
                session['user'] = username
                return redirect('/dashboard')

    return render_template("error.html", message="Login failed. Invalid credentials.")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template('dashboard.html', user=session['user'])

@app.route('/generate_bill')
def generate_bill():
    if 'user' not in session:
        return redirect('/')
    return render_template('generate_bill.html')

@app.route('/calculate')
def calculate():
    if 'user' not in session:
        return redirect('/')

    consumer = request.args.get('consumer')
    meter = request.args.get('meter')
    conn_type = request.args.get('type')
    units = int(request.args.get('units'))

    # Calculate bill
    amount = 0
    if conn_type == 'domestic':
        if units <= 100:
            amount = 0
        elif units <= 200:
            amount = (units - 100) * 2.35
        elif units <= 400:
            amount = 100 * 2.35 + (units - 200) * 4.70
        elif units <= 500:
            amount = 100 * 2.35 + 200 * 4.70 + (units - 400) * 6.30
        elif units <= 600:
            amount = 100 * 2.35 + 200 * 4.70 + 100 * 6.30 + (units - 500) * 8.40
        elif units <= 800:
            amount = 100 * 2.35 + 200 * 4.70 + 100 * 6.30 + 100 * 8.40 + (units - 600) * 9.45
        elif units <= 1000:
            amount = 100 * 2.35 + 200 * 4.70 + 100 * 6.30 + 100 * 8.40 + 200 * 9.45 + (units - 800) * 10.50
        else:
            amount = 100 * 2.35 + 200 * 4.70 + 100 * 6.30 + 100 * 8.40 + 200 * 9.45 + 200 * 10.50 + (units - 1000) * 11.55
    elif conn_type == 'commercial':
        if units <= 100:
            amount = units * 6.00
        elif units <= 500:
            amount = 100 * 6.00 + (units - 100) * 7.00
        else:
            amount = 100 * 6.00 + 400 * 7.00 + (units - 500) * 8.00

    date_str = time.strftime("%Y-%m-%d %H:%M:%S")

    with open(BILLS_FILE, 'a') as f:
        f.write(f"{session['user']}|{consumer}|{meter}|{conn_type}|{units}|{amount:.2f}|Not Paid|{date_str}\n")

    return render_template('bill_result.html', user=session['user'], consumer=consumer,
                           meter=meter, type=conn_type, units=units, amount=f"{amount:.2f}", status="Not Paid", date=date_str)

@app.route('/bill_history')
def bill_history():
    if 'user' not in session:
        return redirect('/')

    bills = []
    total_unpaid = 0

    if os.path.exists(BILLS_FILE):
        with open(BILLS_FILE, 'r') as f:
            for line in f:
                data = line.strip().split('|')
                if data[0] == session['user']:
                    bills.append(data)
                    if data[6] == "Not Paid":
                        total_unpaid += float(data[5])

    return render_template('bill_history.html', bills=bills, total_unpaid=total_unpaid)

@app.route('/search_meter')
def search_meter():
    meter = request.args.get('meter')
    found_status = "Not Found"

    if meter and os.path.exists(BILLS_FILE):
        with open(BILLS_FILE, 'r') as f:
            for line in f:
                data = line.strip().split('|')
                if data[2] == meter:
                    found_status = data[6]
                    break

    return render_template('search_meter.html', meter=meter, status=found_status)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", message="Page not found."), 404

import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)