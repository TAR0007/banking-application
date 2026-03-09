 Advanced Banking System (Tkinter)

A modern, feature-rich **Banking Interface** built with Python's **Tkinter GUI toolkit** and **SQLite3 database**. This project demonstrates account management, secure login, and transaction tracking in a desktop app format.

---

  Features

 User Management
- User **Registration & Login** with password hashing.
- Each user has a personal balance, transaction history, and credentials stored securely in SQLite.

 Banking Operations
- **Deposit, Withdraw, and Transfer** money between accounts.
- **Live Balance Update** and **Transaction History Log**.
- **Export Transactions to CSV** for record-keeping.

 Admin Dashboard
- Admin can **view all users**, check balances, and reset passwords.
- Secure access (admin credentials stored separately).

 GUI Highlights
- Built using **Tkinter** + **ttk** themed widgets.
- Modular design with multiple windows (login, dashboard, admin panel).
- Smooth navigation and clean modern layout.

---

 Installation

1. Clone this repository or copy the project files.
2. Ensure you have Python 3.8+ installed.
3. Install dependencies (Tkinter is included by default):
   ```bash
   pip install tk
   ```
4. Run the application:
   ```bash
   python Advanced_Banking_Tkinter.py
   ```

---

  Default Accounts
| Username | Password  | Balance |
|-----------|-----------|----------|
| alice     | alice123  | ₹1000   |
| bob       | bob123    | ₹500    |
| admin     | admin123  | Admin Panel |

---

 Database Structure

The app uses a local **SQLite3** database `bank.db` with two main tables:

 `users`
| Field | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| username | TEXT | Unique username |
| password | TEXT | Hashed password |
| balance | REAL | Account balance |

 `transactions`
| Field | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| username | TEXT | Linked user |
| type | TEXT | Deposit / Withdraw / Transfer |
| amount | REAL | Transaction amount |
| date | TEXT | Timestamp |

---

 Future Enhancements
- Add **QR Payment simulation**.
- Integrate **OTP verification** for security.
- Dark / Light mode themes.
- Integration with APIs for live exchange rates or account validation.

---

 Tech Stack
- Language: Python 3.x
- GUI: Tkinter / ttk
- Database: SQLite3
- Libraries: hashlib, csv, datetime
---

 Developed by TAR & Aaron
A showcase of Python desktop application design using Tkinter with a secure, modular approach.
