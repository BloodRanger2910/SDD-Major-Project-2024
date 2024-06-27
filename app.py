from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import bcrypt
from datetime import datetime
import webbrowser
import threading
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your own secret key

# Database setup
conn = sqlite3.connect('finance_manager.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, username TEXT, category TEXT, expense TEXT, amount REAL, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS budgets (id INTEGER PRIMARY KEY, username TEXT, category TEXT, amount REAL, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY, username TEXT, name TEXT, initial_amount REAL, remaining_amount REAL)''')
conn.commit()

def get_current_user():
    return session['username'] if 'username' in session else None

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('main'))
    return render_template('login.html')

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
            return redirect(url_for('main'))
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

@app.route('/main')
def main():
    current_user = get_current_user()
    if current_user:
        return render_template('main.html', username=current_user)
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/overview')
def overview():
    current_user = get_current_user()
    if current_user:
        return render_template('overview.html')
    return redirect(url_for('login'))

@app.route('/expense', methods=['GET', 'POST'])
def expense():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        category = request.form['category']
        expense_name = request.form['expense']
        amount = request.form['amount']
        date = request.form['date']

        if category and expense_name and amount and date:
            c.execute("INSERT INTO expenses (username, category, expense, amount, date) VALUES (?, ?, ?, ?, ?)", 
                      (current_user, category, expense_name, float(amount), date))
            conn.commit()
            flash('Expense added successfully', 'success')
        else:
            flash('Please enter all details', 'error')
    
    c.execute("SELECT category, expense, amount, date FROM expenses WHERE username=? ORDER BY date DESC LIMIT 10", (current_user,))
    expenses = c.fetchall()
    return render_template('expense.html', expenses=expenses, current_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/submit_expense', methods=['POST'])
def submit_expense():
    # Handle form data
    category = request.form.get('category')
    expense = request.form.get('expense')
    amount = request.form.get('amount')
    currency = request.form.get('currency')
    payment_method = request.form.get('payment_method')
    tags = request.form.get('tags')
    recurrence = request.form.get('recurrence')

    # Handle file uploads
    attachments = request.files.getlist('attachments')
    attachment_paths = []
    for attachment in attachments:
        if attachment.filename != '':
            attachment_path = os.path.join(app.config['UPLOAD_FOLDER'], attachment.filename)
            attachment.save(attachment_path)
            attachment_paths.append(attachment_path)

    # Save expense data and attachment paths to database or process further as needed

    return jsonify({'message': 'Expense submitted successfully'})

@app.route('/budget')
def budget():
    current_user = get_current_user()
    if current_user:
        return render_template('budget.html')
    return redirect(url_for('login'))

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

@app.route('/reporting')
def reporting():
    current_user = get_current_user()
    if current_user:
        return render_template('reporting.html')
    return redirect(url_for('login'))

@app.route('/income')
def income():
    current_user = get_current_user()
    if current_user:
        return render_template('income.html')
    return redirect(url_for('login'))

@app.route('/help')
def help():
    current_user = get_current_user()
    if current_user:
        return render_template('help.html')
    return redirect(url_for('login'))

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



def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        threading.Timer(1, open_browser).start()
    app.run(debug=True)
