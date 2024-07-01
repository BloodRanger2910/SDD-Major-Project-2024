from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import bcrypt
from datetime import datetime
import webbrowser
import threading
import os
from pathlib import Path

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Determine common application data folder based on platform
if os.name == 'nt':  # Windows
    common_data_folder = os.getenv('ALLUSERSPROFILE')
elif os.name == 'posix':  # Linux, MacOS, etc.
    common_data_folder = '/var/lib'  # Adjust for specific Unix-like systems if needed

# Ensure the folder exists, create if necessary
database_folder = os.path.join(common_data_folder, 'Maahir Ahmed', 'Financial Manager Application')
Path(database_folder).mkdir(parents=True, exist_ok=True)

database_path = os.path.join(database_folder, 'finance_manager.db')
# Database setup
conn = sqlite3.connect('finance_manager.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                balance REAL DEFAULT 0.0
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                category TEXT,
                expense_name TEXT,
                amount REAL,
                payment_method TEXT,
                date TEXT,
                tags TEXT,
                attachments TEXT,
                FOREIGN KEY(username) REFERENCES users(id)
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY,
                username TEXT,
                name TEXT,
                initial_amount REAL,
                remaining_amount REAL
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS incomes (
                id INTEGER PRIMARY KEY,
                username TEXT,
                source TEXT,
                amount REAL,
                date TEXT
            )''')
c.execute('''CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY,
                username TEXT,
                category TEXT,
                budget_amount REAL,
                FOREIGN KEY(username) REFERENCES users(username)
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS saving_goals (
                id INTEGER PRIMARY KEY,
                username TEXT,
                goal_name TEXT,
                target_amount REAL,
                saved_amount REAL DEFAULT 0.0,
                FOREIGN KEY(username) REFERENCES users(username)
            )''')
conn.commit()

def get_current_user():
    return session['username'] if 'username' in session else None

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('main'))
    return render_template('login.html')

#Login/Register Pages
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        if not username or not password:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('login'))

        c.execute("SELECT password_hash FROM users WHERE username=?", (username,))
        result = c.fetchone()
        if result and bcrypt.checkpw(password, result[0]):
            session['username'] = username
            return redirect(url_for('disclaimer'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        confirm_password = request.form['confirm_password'].encode('utf-8')

        if not username or not password or not confirm_password:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template('register.html', error="Passwords do not match")

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        if c.fetchone():
            flash('Username already exists', 'error')
        else:
            password_hash = bcrypt.hashpw(password, bcrypt.gensalt())
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            flash('User registered successfully', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

#Home Page
@app.route('/main')
def main():
    current_user = get_current_user()
    if current_user:
        total_income = get_total_income(current_user)
        total_expenses = get_total_expenses(current_user)
        balance = total_income - total_expenses

        recent_transactions = get_recent_income(current_user)
        budget_overview = get_budget_overview(current_user)
        
        net_savings = total_income - total_expenses

        return render_template(
            'main.html',
            username=current_user,
            balance=balance,
            recent_transactions=recent_transactions,
            budget_overview=budget_overview,
            total_income=total_income,
            total_expenses=total_expenses,
            net_savings=net_savings
        )
    return redirect(url_for('login'))

def get_total_expenses(username):
    c.execute("SELECT SUM(amount) FROM expenses WHERE username=?", (username,))
    return c.fetchone()[0] or 0

def get_total_income(username):
    c.execute("SELECT SUM(amount) FROM incomes WHERE username=?", (username,))
    return c.fetchone()[0] or 0

def get_budget_overview(username):
    c.execute("""
        SELECT b.category, IFNULL(SUM(e.amount), 0) AS spent, b.budget_amount
        FROM budgets b
        LEFT JOIN expenses e ON b.username = e.username AND b.category = e.category
        WHERE b.username=?
        GROUP BY b.category, b.budget_amount
    """, (username,))
    return c.fetchall()

def get_recent_income(username):
    c.execute("""
        SELECT date, description, amount 
        FROM (
            SELECT date, source AS description, amount FROM incomes WHERE username=?
            UNION ALL
            SELECT date, expense_name AS description, amount FROM expenses WHERE username=?
        )
        ORDER BY date DESC LIMIT 5
    """, (username, username))
    return c.fetchall()

#Income Tracking
@app.route('/income', methods=['GET', 'POST'])
def income():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        source = request.form['source']
        amount = request.form['amount']
        date = request.form['date']

        # Convert date to 'dd-mm-yyyy' format for storage in the database
        formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d-%m-%Y')

        if source and amount and formatted_date:
            c.execute("INSERT INTO incomes (username, source, amount, date) VALUES (?, ?, ?, ?)", 
                      (current_user, source, float(amount), formatted_date))
            conn.commit()
            flash('Income added successfully', 'success')
        else:
            flash('Please enter all details', 'error')

    # Fetch incomes and sort by date in ascending order
    c.execute("SELECT source, amount, date FROM incomes WHERE username=? ORDER BY date DESC", (current_user,))
    incomes = c.fetchall()
    return render_template('income.html', incomes=incomes, current_date=datetime.now().strftime('%d-%m-%Y'))


#Expense Tracking
@app.route('/expense', methods=['GET', 'POST'])
def expense():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        category = request.form['category']
        expense_name = request.form['expense_name']
        amount = float(request.form['amount'])
        payment_method = request.form['payment_method']
        date = request.form['date']
        attachments = request.files.getlist('attachments')
        
        # Handle file uploads
        attachment_paths = []
        for attachment in attachments:
            if attachment.filename != '':
                attachment_path = os.path.join(app.config['UPLOAD_FOLDER'], attachment.filename)
                attachment.save(attachment_path)
                attachment_paths.append(attachment_path)

        if category and expense_name and amount and date:
            c.execute("INSERT INTO expenses (username, category, expense_name, amount, payment_method, date, attachments) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                      (current_user, category, expense_name, amount, payment_method, date, None))
            conn.commit()
            flash('Expense added successfully', 'success')
        else:
            flash('Please enter all details', 'error')
    
    c.execute("SELECT category, expense_name, amount, date FROM expenses WHERE username=? ORDER BY date DESC LIMIT 10", (current_user,))
    expenses = c.fetchall()
    return render_template('expense.html', expenses=expenses, current_date=datetime.now().strftime('%Y-%m-%d'))

# Budget Management
@app.route('/budget', methods=['GET', 'POST'])
def budget():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'category' in request.form:
            category = request.form['category']
            budget_amount = float(request.form['budget_amount'])
            
            # Check if budget already exists for this category
            c.execute("SELECT id FROM budgets WHERE username=? AND category=?", (current_user, category))
            existing_budget = c.fetchone()

            if existing_budget:
                # Update existing budget
                c.execute("UPDATE budgets SET budget_amount=? WHERE id=?", (budget_amount, existing_budget[0]))
                conn.commit()
                flash('Budget updated successfully', 'success')
            else:
                # Insert new budget
                c.execute("INSERT INTO budgets (username, category, budget_amount) VALUES (?, ?, ?)", 
                          (current_user, category, budget_amount))
                conn.commit()
                flash('Budget added successfully', 'success')

    # Fetch all budgets for the current user
    c.execute("SELECT category, budget_amount FROM budgets WHERE username=?", (current_user,))
    budgets = c.fetchall()
    return render_template('budget.html', budgets=budgets)


#Debt Pages
@app.route('/debt', methods=['GET', 'POST'])
def debt():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        debt_name = request.form['debt_name']
        initial_amount = float(request.form['initial_amount'])
        c.execute("INSERT INTO debts (username, name, initial_amount, remaining_amount) VALUES (?, ?, ?, ?)", (current_user, debt_name, initial_amount, initial_amount))
        conn.commit()
        flash("Debt added successfully", "success")
        return redirect(url_for('debt'))

    c.execute("SELECT id, name, remaining_amount FROM debts WHERE username=?", (current_user,))
    debts = c.fetchall()
    # Convert fetched debts to dictionaries
    debts = [{'id': debt[0], 'name': debt[1], 'remaining_amount': debt[2]} for debt in debts]
    return render_template('debt.html', debts=debts)

@app.route('/update_debt/<int:debt_id>', methods=['POST'])
def update_debt(debt_id):
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))

    if 'action' in request.form:
        action = request.form['action']
        
        if action == 'delete':
            # Delete the debt
            c.execute("DELETE FROM debts WHERE id=?", (debt_id,))
            conn.commit()
            flash("Debt deleted successfully", "success")
        elif action in ['plus', 'minus']:
            # Handle update (add or subtract amount)
            amount_str = request.form['amount'].strip()
            
            if amount_str:
                try:
                    amount = float(amount_str)
                    if action == 'plus':
                        c.execute("UPDATE debts SET remaining_amount = remaining_amount + ? WHERE id=?", (amount, debt_id))
                    elif action == 'minus':
                        c.execute("UPDATE debts SET remaining_amount = remaining_amount - ? WHERE id=?", (amount, debt_id))
                    conn.commit()
                    flash("Debt updated successfully", "success")
                except ValueError:
                    flash("Invalid amount entered", "error")
            else:
                flash("Please enter a valid amount", "error")
        else:
            flash("Invalid action specified", "error")
    else:
        flash("Action not specified", "error")

    return redirect(url_for('debt'))

@app.route('/delete_debt/<int:debt_id>', methods=['POST'])
def delete_debt(debt_id):
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))

    # Fetch the debt from the database to verify ownership
    c.execute("SELECT id FROM debts WHERE id=? AND username=?", (debt_id, current_user))
    debt = c.fetchone()
    if not debt:
        flash('Debt not found or you do not have permission to delete it', 'error')
        return redirect(url_for('debt'))

    # Perform deletion from the database
    c.execute("DELETE FROM debts WHERE id=?", (debt_id,))
    conn.commit()

    flash('Debt deleted successfully', 'success')
    return redirect(url_for('debt'))

@app.route('/debt_summary')
def debt_summary():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))

    c.execute("SELECT name, initial_amount, remaining_amount FROM debts WHERE username=?", (current_user,))
    debts = c.fetchall()
    # Convert fetched debts to dictionaries
    debts = [{'name': debt[0], 'initial_amount': debt[1], 'remaining_amount': debt[2]} for debt in debts]
    return jsonify(debts)

#Finanacial Reporting Page
@app.route('/reporting')
def reporting():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))

    # Expense report data
    c.execute("SELECT category, amount, date FROM expenses WHERE username=? ORDER BY date DESC", (current_user,))
    expenses = c.fetchall()
    c.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as total
        FROM expenses
        WHERE username=?
        GROUP BY month
        ORDER BY month DESC
    """, (current_user,))
    monthly_expense_summary = c.fetchall()

    # Income report data
    c.execute("SELECT source, amount, date FROM incomes WHERE username=? ORDER BY date DESC", (current_user,))
    incomes = c.fetchall()
    c.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as total
        FROM incomes
        WHERE username=?
        GROUP BY month
        ORDER BY month DESC
    """, (current_user,))
    monthly_income_summary = c.fetchall()

    # Budget report data
    c.execute("SELECT category, budget_amount FROM budgets WHERE username=?", (current_user,))
    budgets = c.fetchall()
    c.execute("""
        SELECT category, SUM(amount) as total_spent
        FROM expenses
        WHERE username=?
        GROUP BY category
    """, (current_user,))
    expenses_per_category = c.fetchall()

    # Financial statement data
    c.execute("SELECT SUM(amount) FROM incomes WHERE username=?", (current_user,))
    total_income = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM expenses WHERE username=?", (current_user,))
    total_expenses = c.fetchone()[0] or 0
    balance = total_income - total_expenses

    # Debt report data
    c.execute("SELECT name, initial_amount, remaining_amount FROM debts WHERE username=?", (current_user,))
    debts = c.fetchall()

    return render_template('reporting.html', expenses=expenses, monthly_expense_summary=monthly_expense_summary,
                           incomes=incomes, monthly_income_summary=monthly_income_summary, budgets=budgets,
                           expenses_per_category=expenses_per_category, total_income=total_income,
                           total_expenses=total_expenses, balance=balance, debts=debts)

#Disclaimer
@app.route('/disclaimer')
def disclaimer():
    current_user = get_current_user()
    if current_user:
        return render_template("disclaimer.html")
    if not current_user:
        return redirect(url_for('login'))
    
#Help Page
@app.route('/help')
def help():
    current_user = get_current_user()
    if current_user:
        return render_template('help.html')
    return redirect(url_for('login'))

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        threading.Timer(1, open_browser).start()
    app.run(debug=True)
