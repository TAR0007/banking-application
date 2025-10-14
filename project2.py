

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import hashlib
import csv
import os
from datetime import datetime

DB_FILE = 'banking.db'

# ---------------------- Database helpers ----------------------
class Database:
    def __init__(self, path=DB_FILE):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cur = self.conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                fullname TEXT,
                balance REAL DEFAULT 0.0,
                is_admin INTEGER DEFAULT 0
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount REAL,
                counterparty TEXT,
                note TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        self.conn.commit()
        # create default users
        try:
            self.create_user('alice', 'alice123', fullname='Alice Doe', balance=1000.0)
            self.create_user('bob', 'bob123', fullname='Bob Roe', balance=500.0)
        except Exception:
            pass

    def hash_password(self, pwd):
        return hashlib.sha256(pwd.encode('utf-8')).hexdigest()

    def create_user(self, username, password, fullname='', balance=0.0, is_admin=0):
        cur = self.conn.cursor()
        hp = self.hash_password(password)
        cur.execute('INSERT INTO users (username, password, fullname, balance, is_admin) VALUES (?,?,?,?,?)',
                    (username, hp, fullname, balance, is_admin))
        self.conn.commit()
        return cur.lastrowid

    def authenticate(self, username, password):
        cur = self.conn.cursor()
        cur.execute('SELECT id, password, is_admin FROM users WHERE username=?', (username,))
        row = cur.fetchone()
        if not row:
            return None
        uid, hp, is_admin = row
        if self.hash_password(password) == hp:
            return {'id': uid, 'username': username, 'is_admin': bool(is_admin)}
        return None

    def get_user(self, user_id=None, username=None):
        cur = self.conn.cursor()
        if user_id:
            cur.execute('SELECT id, username, fullname, balance, is_admin FROM users WHERE id=?', (user_id,))
        else:
            cur.execute('SELECT id, username, fullname, balance, is_admin FROM users WHERE username=?', (username,))
        row = cur.fetchone()
        if row:
            return dict(zip(['id','username','fullname','balance','is_admin'], row))
        return None

    def update_balance(self, user_id, new_balance):
        cur = self.conn.cursor()
        cur.execute('UPDATE users SET balance=? WHERE id=?', (new_balance, user_id))
        self.conn.commit()

    def add_transaction(self, user_id, tx_type, amount, counterparty='', note=''):
        cur = self.conn.cursor()
        ts = datetime.utcnow().isoformat()
        cur.execute('INSERT INTO transactions (user_id, type, amount, counterparty, note, timestamp) VALUES (?,?,?,?,?,?)',
                    (user_id, tx_type, amount, counterparty, note, ts))
        self.conn.commit()
        return cur.lastrowid

    def get_transactions(self, user_id, limit=200):
        cur = self.conn.cursor()
        cur.execute('SELECT type, amount, counterparty, note, timestamp FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT ?', (user_id, limit))
        return cur.fetchall()

    def find_user_by_username(self, username):
        cur = self.conn.cursor()
        cur.execute('SELECT id, username FROM users WHERE username=?', (username,))
        return cur.fetchone()

    def list_users(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id, username, fullname, balance, is_admin FROM users')
        return cur.fetchall()

    def reset_password(self, username, new_password):
        cur = self.conn.cursor()
        hp = self.hash_password(new_password)
        cur.execute('UPDATE users SET password=? WHERE username=?', (hp, username))
        self.conn.commit()

# ---------------------- App UI ----------------------

class BankingApp(tk.Tk):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.title('Advanced Banking Interface')
        self.geometry('920x620')
        self.minsize(900, 600)
        self.style = ttk.Style(self)
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        # container
        self.container = ttk.Frame(self)
        self.container.pack(fill='both', expand=True)

        self.current_user = None

        # frames
        self.frames = {}
        for F in (LoginFrame, RegisterFrame, DashboardFrame, AdminFrame):
            frame = F(self.container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame('LoginFrame')

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()
        if hasattr(frame, 'on_show'):
            frame.on_show()

    def login(self, username, password):
        info = self.db.authenticate(username, password)
        if info:
            self.current_user = self.db.get_user(user_id=info['id'])
            if info['is_admin']:
                self.show_frame('AdminFrame')
            else:
                self.show_frame('DashboardFrame')
            return True
        return False

    def logout(self):
        self.current_user = None
        self.show_frame('LoginFrame')

# ---------------------- Individual Frames ----------------------

class LoginFrame(ttk.Frame):
    def __init__(self, parent, app: BankingApp):
        super().__init__(parent)
        self.app = app
        pad = 12
        self.columnconfigure(0, weight=1)

        title = ttk.Label(self, text='Welcome to Neo Bank', font=('Helvetica', 20, 'bold'))
        title.grid(row=0, column=0, pady=(20,10))

        card = ttk.Frame(self, padding=20, relief='raised')
        card.grid(row=1, column=0, padx=30, pady=20)

        ttk.Label(card, text='Username').grid(row=0, column=0, sticky='w')
        self.username = ttk.Entry(card)
        self.username.grid(row=1, column=0, sticky='we', pady=(0,8))

        ttk.Label(card, text='Password').grid(row=2, column=0, sticky='w')
        self.password = ttk.Entry(card, show='*')
        self.password.grid(row=3, column=0, sticky='we', pady=(0,8))

        btn_frame = ttk.Frame(card)
        btn_frame.grid(row=4, column=0, pady=(8,0))

        login_btn = ttk.Button(btn_frame, text='Login', command=self.on_login)
        login_btn.grid(row=0, column=0, padx=(0,6))
        reg_btn = ttk.Button(btn_frame, text='Register', command=lambda: app.show_frame('RegisterFrame'))
        reg_btn.grid(row=0, column=1)

        help_lbl = ttk.Label(self, text='Use default test accounts: alice/alice123 or bob/bob123', foreground='gray')
        help_lbl.grid(row=2, column=0)

    def on_login(self):
        u = self.username.get().strip()
        p = self.password.get().strip()
        if not u or not p:
            messagebox.showwarning('Input error', 'Please enter username and password')
            return
        if self.app.login(u, p):
            self.username.delete(0, 'end')
            self.password.delete(0, 'end')
        else:
            messagebox.showerror('Login failed', 'Invalid username or password')

class RegisterFrame(ttk.Frame):
    def __init__(self, parent, app: BankingApp):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text='Register', font=('Helvetica', 18, 'bold')).pack(pady=10)
        frm = ttk.Frame(self, padding=12, relief='ridge')
        frm.pack(padx=10, pady=10)

        ttk.Label(frm, text='Username').grid(row=0, column=0, sticky='w')
        self.username = ttk.Entry(frm)
        self.username.grid(row=1, column=0, sticky='we')

        ttk.Label(frm, text='Full name').grid(row=2, column=0, sticky='w')
        self.fullname = ttk.Entry(frm)
        self.fullname.grid(row=3, column=0, sticky='we')

        ttk.Label(frm, text='Password').grid(row=4, column=0, sticky='w')
        self.password = ttk.Entry(frm, show='*')
        self.password.grid(row=5, column=0, sticky='we')

        ttk.Label(frm, text='Initial Deposit').grid(row=6, column=0, sticky='w')
        self.deposit = ttk.Entry(frm)
        self.deposit.grid(row=7, column=0, sticky='we')

        ttk.Button(frm, text='Create Account', command=self.create_account).grid(row=8, column=0, pady=8)
        ttk.Button(frm, text='Back to Login', command=lambda: app.show_frame('LoginFrame')).grid(row=9, column=0)

    def create_account(self):
        u = self.username.get().strip()
        fn = self.fullname.get().strip()
        p = self.password.get().strip()
        try:
            initial = float(self.deposit.get().strip() or 0.0)
        except ValueError:
            messagebox.showerror('Invalid', 'Initial deposit must be a number')
            return
        if not u or not p:
            messagebox.showwarning('Missing', 'Username and password required')
            return
        try:
            self.app.db.create_user(u, p, fullname=fn, balance=initial)
            messagebox.showinfo('Success', 'Account created. You can login now.')
            self.app.show_frame('LoginFrame')
        except sqlite3.IntegrityError:
            messagebox.showerror('Error', 'Username already exists')

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, app: BankingApp):
        super().__init__(parent)
        self.app = app
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        top = ttk.Frame(self)
        top.pack(fill='x', padx=12, pady=(12,6))

        self.welcome = ttk.Label(top, text='', font=('Helvetica', 16, 'bold'))
        self.welcome.pack(side='left')

        ttk.Button(top, text='Logout', command=self.app.logout).pack(side='right')

        # Main area
        main = ttk.Frame(self)
        main.pack(fill='both', expand=True, padx=12, pady=6)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=2)

        # Left: quick actions + balance
        left = ttk.Frame(main, padding=10, relief='groove')
        left.grid(row=0, column=0, sticky='nsew', padx=(0,8), pady=6)
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text='Account Balance', font=('Helvetica', 12, 'bold')).pack()
        self.balance_lbl = ttk.Label(left, text='₹0.00', font=('Helvetica', 18))
        self.balance_lbl.pack(pady=6)

        ttk.Button(left, text='Deposit', command=self.deposit_dialog).pack(fill='x', pady=4)
        ttk.Button(left, text='Withdraw', command=self.withdraw_dialog).pack(fill='x', pady=4)
        ttk.Button(left, text='Transfer', command=self.transfer_dialog).pack(fill='x', pady=4)
        ttk.Button(left, text='Export Statement', command=self.export_statement).pack(fill='x', pady=4)

        # Right: transactions
        right = ttk.Frame(main, padding=10, relief='ridge')
        right.grid(row=0, column=1, sticky='nsew', pady=6)
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text='Recent Transactions', font=('Helvetica', 12, 'bold')).grid(row=0, column=0, sticky='w')
        self.tx_tree = ttk.Treeview(right, columns=('type','amount','counterparty','note','timestamp'), show='headings')
        for col, w in [('type',80), ('amount',80), ('counterparty',120), ('note',200), ('timestamp',180)]:
            self.tx_tree.heading(col, text=col.title())
            self.tx_tree.column(col, width=w, anchor='w')
        self.tx_tree.grid(row=1, column=0, sticky='nsew', pady=6)
        right.rowconfigure(1, weight=1)

        # quick stats below
        stats = ttk.Frame(self)
        stats.pack(fill='x', padx=12, pady=(0,12))
        self.stat_deposits = ttk.Label(stats, text='Deposits: 0')
        self.stat_withdraws = ttk.Label(stats, text='Withdrawals: 0')
        self.stat_transfers = ttk.Label(stats, text='Transfers: 0')
        self.stat_deposits.pack(side='left', padx=8)
        self.stat_withdraws.pack(side='left', padx=8)
        self.stat_transfers.pack(side='left', padx=8)

    def on_show(self):
        user = self.app.current_user
        self.welcome.config(text=f"Hello, {user.get('fullname') or user.get('username')}")
        self.refresh_dashboard()

    def refresh_dashboard(self):
        user = self.app.current_user
        u = self.app.db.get_user(user_id=user['id'])
        self.app.current_user = u
        self.balance_lbl.config(text=f'₹{u["balance"]:,.2f}')
        # load transactions
        for row in self.tx_tree.get_children():
            self.tx_tree.delete(row)
        txs = self.app.db.get_transactions(u['id'], limit=200)
        dep = wdr = trf = 0
        for t in txs:
            typ, amt, cp, note, ts = t
            self.tx_tree.insert('', 'end', values=(typ, f'{amt:.2f}', cp or '', note or '', ts.replace('T',' ')))
            if typ.lower() == 'deposit':
                dep += 1
            elif typ.lower() == 'withdraw':
                wdr += 1
            else:
                trf += 1
        self.stat_deposits.config(text=f'Deposits: {dep}')
        self.stat_withdraws.config(text=f'Withdrawals: {wdr}')
        self.stat_transfers.config(text=f'Transfers: {trf}')

    # ---------------- dialog actions ----------------
    def deposit_dialog(self):
        amt = simpledialog.askfloat('Deposit', 'Amount to deposit', minvalue=0.01)
        if not amt:
            return
        uid = self.app.current_user['id']
        user = self.app.db.get_user(user_id=uid)
        newbal = user['balance'] + amt
        self.app.db.update_balance(uid, newbal)
        self.app.db.add_transaction(uid, 'Deposit', amt, counterparty='', note='Deposit via app')
        messagebox.showinfo('Success', f'Deposited ₹{amt:.2f}')
        self.refresh_dashboard()

    def withdraw_dialog(self):
        amt = simpledialog.askfloat('Withdraw', 'Amount to withdraw', minvalue=0.01)
        if not amt:
            return
        uid = self.app.current_user['id']
        user = self.app.db.get_user(user_id=uid)
        if amt > user['balance']:
            messagebox.showerror('Insufficient', 'Not enough balance')
            return
        newbal = user['balance'] - amt
        self.app.db.update_balance(uid, newbal)
        self.app.db.add_transaction(uid, 'Withdraw', -amt, counterparty='', note='Withdrawal via app')
        messagebox.showinfo('Success', f'Withdrawn ₹{amt:.2f}')
        self.refresh_dashboard()

    def transfer_dialog(self):
        frm = TransferDialog(self, self.app)
        self.wait_window(frm)
        # refresh after dialog closes
        self.refresh_dashboard()

    def export_statement(self):
        uid = self.app.current_user['id']
        txs = self.app.db.get_transactions(uid, limit=5000)
        if not txs:
            messagebox.showinfo('No data', 'No transactions to export')
            return
        fname = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files','*.csv')])
        if not fname:
            return
        with open(fname, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Type','Amount','Counterparty','Note','Timestamp'])
            for t in reversed(txs):
                writer.writerow(t)
        messagebox.showinfo('Exported', f'Statement saved to {fname}')

class TransferDialog(tk.Toplevel):
    def __init__(self, parent, app: BankingApp):
        super().__init__(parent)
        self.app = app
        self.title('Transfer Funds')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frm = ttk.Frame(self, padding=12)
        frm.grid(row=0, column=0)

        ttk.Label(frm, text='To Username').grid(row=0, column=0, sticky='w')
        self.to_user = ttk.Entry(frm)
        self.to_user.grid(row=1, column=0, sticky='we')

        ttk.Label(frm, text='Amount').grid(row=2, column=0, sticky='w')
        self.amount = ttk.Entry(frm)
        self.amount.grid(row=3, column=0, sticky='we')

        ttk.Label(frm, text='Note (optional)').grid(row=4, column=0, sticky='w')
        self.note = ttk.Entry(frm)
        self.note.grid(row=5, column=0, sticky='we')

        ttk.Button(frm, text='Send', command=self.on_send).grid(row=6, column=0, pady=8)

    def on_send(self):
        to = self.to_user.get().strip()
        try:
            amt = float(self.amount.get().strip())
        except Exception:
            messagebox.showerror('Invalid', 'Enter valid amount')
            return
        if not to:
            messagebox.showerror('Invalid', 'Enter target username')
            return
        uid = self.app.current_user['id']
        if to == self.app.current_user['username']:
            messagebox.showerror('Invalid', 'Cannot transfer to self')
            return
        found = self.app.db.find_user_by_username(to)
        if not found:
            messagebox.showerror('Not found', 'Target user not found')
            return
        if amt <= 0:
            messagebox.showerror('Invalid', 'Amount must be positive')
            return
        sender = self.app.db.get_user(user_id=uid)
        if amt > sender['balance']:
            messagebox.showerror('Insufficient', 'Not enough balance')
            return
        # perform transfer
        receiver_id = found[0]
        new_sender_bal = sender['balance'] - amt
        receiver = self.app.db.get_user(user_id=receiver_id)
        new_receiver_bal = receiver['balance'] + amt
        self.app.db.update_balance(uid, new_sender_bal)
        self.app.db.update_balance(receiver_id, new_receiver_bal)
        self.app.db.add_transaction(uid, 'Transfer Out', -amt, counterparty=to, note=self.note.get().strip())
        self.app.db.add_transaction(receiver_id, 'Transfer In', amt, counterparty=self.app.current_user['username'], note=self.note.get().strip())
        messagebox.showinfo('Success', f'Transferred ₹{amt:.2f} to {to}')
        self.destroy()

class AdminFrame(ttk.Frame):
    def __init__(self, parent, app: BankingApp):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text='Admin Panel', font=('Helvetica', 18, 'bold')).pack(pady=8)
        top = ttk.Frame(self)
        top.pack(fill='x', padx=12)
        ttk.Button(top, text='Logout', command=self.app.logout).pack(side='right')

        self.table = ttk.Treeview(self, columns=('id','username','fullname','balance','is_admin'), show='headings')
        for c,w in [('id',40),('username',120),('fullname',200),('balance',120),('is_admin',80)]:
            self.table.heading(c, text=c.title())
            self.table.column(c, width=w)
        self.table.pack(fill='both', expand=True, padx=12, pady=8)

        btns = ttk.Frame(self)
        btns.pack(pady=6)
        ttk.Button(btns, text='Refresh', command=self.refresh).grid(row=0, column=0, padx=6)
        ttk.Button(btns, text='Reset Password', command=self.reset_password).grid(row=0, column=1, padx=6)

    def on_show(self):
        self.refresh()

    def refresh(self):
        for r in self.table.get_children():
            self.table.delete(r)
        for row in self.app.db.list_users():
            self.table.insert('', 'end', values=row)

    def reset_password(self):
        sel = self.table.selection()
        if not sel:
            messagebox.showwarning('Select', 'Select a user')
            return
        vals = self.table.item(sel[0])['values']
        username = vals[1]
        newpwd = simpledialog.askstring('New Password', f'Enter new password for {username}', show='*')
        if not newpwd:
            return
        self.app.db.reset_password(username, newpwd)
        messagebox.showinfo('Done', 'Password reset')

# ---------------------- Main ----------------------

def main():
    db = Database()
    app = BankingApp(db)
    app.mainloop()

if __name__ == '__main__':
    main()
