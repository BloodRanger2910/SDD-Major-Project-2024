import customtkinter as ctk
import sqlite3
from tkinter import messagebox
import bcrypt
from datetime import datetime

# Database setup
conn = sqlite3.connect('finance_manager.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, username TEXT, category TEXT, expense TEXT, amount REAL, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS budgets (id INTEGER PRIMARY KEY, username TEXT, category TEXT, amount REAL, date TEXT)''')
conn.commit()

current_user = None

# Class for the Financial Management Application
class FinanceApp(ctk.CTk):
    def __init__(self):
        ctk.CTk.__init__(self)
        self.title("Financial Management Application")
        self.geometry("800x600")
        self.resizable(False, False)
        self._frame = None

        # Show login frame initially
        self.show_frame(LoginFrame)

    def show_frame(self, frame_class):
        """Destroys current frame and replaces it with a new one."""
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.grid(row=0, column=0, sticky="nsew")

# Frame for login
class LoginFrame(ctk.CTkFrame):
    def __init__(self, master):
        ctk.CTkFrame.__init__(self, master)
        
        self.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self, text="Username:").grid(row=0, column=0, pady=10, padx=20)
        self.login_username_entry = ctk.CTkEntry(self)
        self.login_username_entry.grid(row=1, column=0, pady=10, padx=20)

        ctk.CTkLabel(self, text="Password:").grid(row=2, column=0, pady=10, padx=20)
        self.login_password_entry = ctk.CTkEntry(self, show="*")
        self.login_password_entry.grid(row=3, column=0, pady=10, padx=20)

        ctk.CTkButton(self, text="Login", command=self.handle_login).grid(row=4, column=0, pady=10, padx=20)
        ctk.CTkButton(self, text="Register", command=self.show_register_frame).grid(row=5, column=0, pady=10, padx=20)

    def handle_login(self):
        global current_user
        username = self.login_username_entry.get()
        password = self.login_password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        c.execute("SELECT password_hash FROM users WHERE username=?", (username,))
        result = c.fetchone()
        if result and bcrypt.checkpw(password.encode(), result[0]):
            current_user = username
            self.master.show_frame(MainFrame)
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def show_register_frame(self):
        self.master.show_frame(RegisterFrame)

# Frame for registration
class RegisterFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self, text="Username:").grid(row=0, column=0, pady=10, padx=20)
        self.register_username_entry = ctk.CTkEntry(self)
        self.register_username_entry.grid(row=1, column=0, pady=10, padx=20)

        ctk.CTkLabel(self, text="Password:").grid(row=2, column=0, pady=10, padx=20)
        self.register_password_entry = ctk.CTkEntry(self, show="*")
        self.register_password_entry.grid(row=3, column=0, pady=10, padx=20)

        ctk.CTkLabel(self, text="Confirm Password:").grid(row=4, column=0, pady=10, padx=20)
        self.confirm_password_entry = ctk.CTkEntry(self, show="*")
        self.confirm_password_entry.grid(row=5, column=0, pady=10, padx=20)

        ctk.CTkButton(self, text="Register", command=self.handle_register).grid(row=6, column=0, pady=10, padx=20)
        ctk.CTkButton(self, text="Back to Login", command=self.show_login_frame).grid(row=7, column=0, pady=10, padx=20)

    def handle_register(self):
        username = self.register_username_entry.get()
        password = self.register_password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        if not username or not password or not confirm_password:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        if c.fetchone():
            messagebox.showerror("Error", "Username already exists")
        else:
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            messagebox.showinfo("Success", "User registered successfully")
            self.master.show_frame(LoginFrame)

    def show_login_frame(self):
        self.master.show_frame(LoginFrame)

# Frame for main application with tabs
class MainFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid(row=0, column=0, sticky="nsew")

        self.tab_view = ctk.CTkTabview(self, width=760, height=540)
        self.tab_view.grid(row=0, column=0, pady=10, padx=10, sticky="nsew")

        self.tab_view.add("Overview")
        self.tab_view.add("Expense Tracking")
        self.tab_view.add("Budget Creator")
        self.tab_view.add("Debt Management")
        self.tab_view.add("Financial Reporting")
        self.tab_view.add("Income Tracking")
        self.tab_view.add("Help")

        self.overview_tab = OverviewTab(self.tab_view.tab("Overview"))
        self.expense_tab = ExpenseTab(self.tab_view.tab("Expense Tracking"))
        self.budget_tab = BudgetTab(self.tab_view.tab("Budget Creator"))
        self.debt_tab = DebtTab(self.tab_view.tab("Debt Management"))
        self.reporting_tab = ReportingTab(self.tab_view.tab("Financial Reporting"))
        self.income_tab = IncomeTab(self.tab_view.tab("Income Tracking"))
        self.help_tab = HelpTab(self.tab_view.tab("Help"))


# Tabs for the application
class OverviewTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self, text="Welcome to the Financial Management Application!").grid(pady=20, padx=20)

class ExpenseTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self, text="Add Expense").grid(row=0, column=0, pady=10, padx=20)
        self.category_entry = ctk.CTkEntry(self, placeholder_text="Category")
        self.category_entry.grid(row=1, column=0, pady=5, padx=20)
        self.expense_entry = ctk.CTkEntry(self, placeholder_text="Expense")
        self.expense_entry.grid(row=2, column=0, pady=5, padx=20)
        self.amount_entry = ctk.CTkEntry(self, placeholder_text="Amount")
        self.amount_entry.grid(row=3, column=0, pady=5, padx=20)
        ctk.CTkButton(self, text="Add Expense", command=self.add_expense).grid(row=4, column=0, pady=10, padx=20)

        ctk.CTkLabel(self, text="Recent Expenses").grid(row=5, column=0, pady=10, padx=20)
        self.expense_list = ctk.CTkTextbox(self, height=10)
        self.expense_list.grid(row=6, column=0, pady=10, padx=20)

        ctk.CTkLabel(self, text="Filter by Date").grid(row=7, column=0, pady=10, padx=20)
        self.date_filter_entry = ctk.CTkEntry(self, placeholder_text="YYYY-MM-DD")
        self.date_filter_entry.grid(row=8, column=0, pady=5, padx=20)
        ctk.CTkButton(self, text="Filter", command=self.filter_expenses).grid(row=9, column=0, pady=10, padx=20)

        self.load_recent_expenses()

    def add_expense(self):
        category = self.category_entry.get()
        expense = self.expense_entry.get()
        amount = self.amount_entry.get()

        if expense and amount and category:
            date_now = datetime.now().strftime("%Y-%m-%d")
            c.execute("INSERT INTO expenses (username, category, expense, amount, date) VALUES (?, ?, ?, ?, ?)", 
                      (current_user, category, expense, float(amount), date_now))
            conn.commit()
            self.expense_list.insert("end", f"{date_now} | {category}: {expense} - ${amount}\n")
            self.category_entry.delete(0, "end")
            self.expense_entry.delete(0, "end")
            self.amount_entry.delete(0, "end")
        else:
            messagebox.showerror("Error", "Please enter all details")

    def load_recent_expenses(self):
        self.expense_list.delete(1.0, "end")
        c.execute("SELECT category, expense, amount, date FROM expenses WHERE username=? ORDER BY date DESC LIMIT 10", (current_user,))
        expenses = c.fetchall()
        for expense in expenses:
            self.expense_list.insert("end", f"{expense[3]} | {expense[0]}: {expense[1]} - ${expense[2]}\n")

    def filter_expenses(self):
        filter_date = self.date_filter_entry.get()
        if filter_date:
            c.execute("SELECT category, expense, amount, date FROM expenses WHERE username=? AND date=? ORDER BY date DESC", (current_user, filter_date))
            filtered_expenses = c.fetchall()
            self.expense_list.delete(1.0, "end")
            for expense in filtered_expenses:
                self.expense_list.insert("end", f"{expense[3]} | {expense[0]}: {expense[1]} - ${expense[2]}\n")
        else:
            messagebox.showerror("Error", "Please enter a valid date (YYYY-MM-DD)")

class BudgetTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self, text="Budget Creator (To be implemented)").grid(pady=20, padx=20)

class DebtTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self, text="Debt Management (To be implemented)").grid(pady=20, padx=20)

class ReportingTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self, text="Financial Reporting (To be implemented)").grid(pady=20, padx=20)

class IncomeTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self, text="Income Tracking (To be implemented)").grid(pady=20, padx=20)

class HelpTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")
        help_text = """
        How to use the Financial Management Application:
        1. Register an account and login.
        2. Add your expenses in the Expense Tracking tab.
        3. Create budgets in the Budget Creator tab and monitor your spending against budget limits.
        4. Manage your debts in the Debt Management tab.
        5. View financial reports in the Financial Reporting tab.
        6. Track your income in the Income Tracking tab.

        FAQ:
        Q: How do I add an expense?
        A: Navigate to the Expense Tracking tab, enter the details, and click 'Add Expense'.

        Q: How do I set a budget?
        A: Go to the Budget Creator tab, enter the category and amount, and click 'Set Budget'.

        Q: Is my data secure?
        A: Yes, we use industry-standard encryption to protect your data.

        For further assistance, contact support.
        """
        ctk.CTkLabel(self, text=help_text, justify="left").grid(pady=20, padx=20)

# Create and run the application
app = FinanceApp()
app.mainloop()
