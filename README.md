# 💸 Expense Tracker

A full-featured expense management web application built with Django. Track personal expenses, split bills with friends, manage group expenses, and keep a unified activity log — all in one place.

---

## 📋 Table of Contents

- [Features](#features)
  - [Authentication](#authentication)
  - [Personal Dashboard](#personal-dashboard)
  - [Friends](#friends)
  - [Groups](#groups)
  - [Settle Up / Payments](#settle-up--payments)
  - [Activity Log](#activity-log)
  - [Django Admin](#django-admin)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Run Locally](#run-locally)
  - [Run with Docker](#run-with-docker)
- [Data Models](#data-models)

---

## ✨ Features

### Authentication

- **User Registration** — Sign up with name, email, and password.
- **OTP Email Verification** — A 4-digit OTP is sent to the user's email via Gmail SMTP. The account is only created after the OTP is verified.
- **Login / Logout** — Session-based authentication with secure login and full session flush on logout.
- **Auto-redirect** — Already logged-in users are automatically redirected away from the register/login pages.
- **Cache Prevention** — Auth pages and dashboards use `@never_cache` to prevent browser back-button access after logout.

---

### Personal Dashboard

Manage your own expenses independently of friends or groups.

| Feature | Details |
|---|---|
| **Add Expense** | Add a new expense with title, amount, category, and date. |
| **Edit Expense** | Update any personal expense. |
| **Delete Expense** | Remove any personal expense (with confirmation). |
| **Search** | Filter expenses by title using a search bar. |
| **Category Filter** | Filter expenses by category (e.g., Food, Travel, etc.). |
| **Sorting** | Sort by date (default), amount ascending, or amount descending. |
| **Statistics** | View total spent, average expense, and current-month total. |
| **Category Breakdown** | See a ranked list of categories by total spending. |
| **Pagination** | Expenses are paginated (3 per page). |

---

### Friends

Add friends and track shared expenses with them.

| Feature | Details |
|---|---|
| **Add Friend** | Search for a registered user by email and send a friend request. |
| **Friend Invite Email** | An email notification is sent to the friend when they are added. |
| **Remove Friend** | Removing a friend is **bidirectional** — both friendship records are deleted. |
| **Mutual Friendship** | When A adds B, the reverse friendship (B → A) is automatically created. |
| **Friend Detail View** | See all shared expenses with a specific friend, total spent, and balance. |
| **Add Shared Expense** | Add an expense shared between you and a friend, selecting who paid. |
| **Custom Split** | Define custom split amounts (not just 50/50) via the split expense form. |
| **Balance Tracking** | The app calculates the net balance — who owes whom and how much. |
| **Delete Friend Expense** | Remove a shared expense (with confirmation). |
| **Pagination** | Friend expenses are paginated (10 per page). |

---

### Groups

Create groups for trips, households, couples, or any shared scenario.

| Feature | Details |
|---|---|
| **Create Group** | Create a group with a name and category (Trip, Home, Couple, Other). |
| **Creator Auto-added** | The group creator is automatically added as a member. |
| **Add Members** | Add members from your existing friend list (excludes existing members). |
| **Leave Group** | Leave a group; if you are the last member, the group is deleted. |
| **Add Group Expense** | Add an expense to the group, specifying who paid. |
| **Custom Member Splits** | Assign a specific share amount to each group member. |
| **Split Validation** | The sum of all member shares must equal the total expense amount. |
| **Atomic Transactions** | Expense and all its splits are saved atomically (all-or-nothing). |
| **Balance Summary** | Per-member net balance calculated from both group splits and 1-on-1 payments. |
| **Delete Group Expense** | Remove a group expense (with confirmation). |
| **Pagination** | Group expenses (10/page) and payment records (5/page) are paginated. |

---

### Settle Up / Payments

Record payments to settle balances between friends, both in 1-on-1 and group contexts.

| Feature | Details |
|---|---|
| **Record Payment** | Log a payment from one person to another to reduce the outstanding balance. |
| **Group Context** | Payments can optionally be tagged to a specific group for accurate group-level balance tracking. |
| **Flexible Payer** | Either the current user or the friend can be marked as the payer. |

---

### Activity Log

A unified, chronological feed of all financial activity.

| Feature | Details |
|---|---|
| **Friend Expenses** | All shared expenses (where you are creator or participant) appear in the feed. |
| **Group Expenses** | All expenses from groups you are a member of appear in the feed. |
| **Group Creations** | Groups you created or joined appear as events in the feed. |
| **Sorted by Date** | All activity types are merged and sorted by date, most recent first. |
| **Pagination** | Activity is paginated (10 items per page). |

---

### Django Admin

All models are registered with Django's built-in admin panel at `/admin/`, providing full CRUD access for site administrators:

- `UserRegistration`
- `Expense`
- `Friend`
- `FriendExpense`
- `Groups`
- `GroupExpense`
- `GroupExpenseSplit`

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.12 |
| **Web Framework** | Django 5.1.1 |
| **Database** | SQLite3 (via Django ORM) |
| **Templating** | Django Templates (HTML + DTL) |
| **Frontend** | HTML, CSS, JavaScript |
| **Email Service** | Gmail SMTP (`django.core.mail`) |
| **Session Management** | Django Sessions (server-side, cookie-based) |
| **Containerization** | Docker, Docker Compose |

---

## 📁 Project Structure

```
ExpenseTracker/
├── expense_proj/          # Django project configuration
│   ├── settings.py        # App settings, DB, email, static files
│   ├── urls.py            # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
│
├── tracker/               # Main application
│   ├── models.py          # All database models
│   ├── views.py           # All view logic
│   ├── urls.py            # App-level URL patterns
│   ├── admin.py           # Admin registrations
│   ├── templates/
│   │   └── tracker/       # HTML templates for every page
│   └── static/
│       └── tracker/       # CSS, JS, images
│
├── manage.py
├── requirements.txt
├── db.sqlite3
├── Dockerfile
└── docker-compose.yml
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- pip

### Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/Yashhp-07/ExpenseTracker.git
cd ExpenseTracker

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. Start the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

> **Note:** To enable OTP email verification, update `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `expense_proj/settings.py` with your own Gmail credentials and [App Password](https://support.google.com/accounts/answer/185833).

---

### Run with Docker

```bash
# Build and start the container (maps host port 8090 → container port 8000)
docker-compose up --build
```

Visit `http://localhost:8090` in your browser.

---

## 🗄 Data Models

| Model | Description |
|---|---|
| `UserRegistration` | Custom user model with name, email, and password. |
| `Expense` | A personal expense belonging to a single user (title, amount, category, date). |
| `Friend` | A directional friendship link between two users. Mutual friendships are auto-created on save. |
| `FriendExpense` | A shared expense between two friends, tracking who paid and how much is owed. |
| `Groups` | A named group with a category and a many-to-many members list. Creator is auto-added as a member. |
| `GroupExpense` | An expense within a group, tracking who paid the full amount. |
| `GroupExpenseSplit` | Represents each member's share of a `GroupExpense`. |
