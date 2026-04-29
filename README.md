# How The Expense Tracker Works (Simple Explanation)

If you are new to full-stack development, all the moving parts can seem overwhelming. Let's break this project down using simple analogies so you understand exactly what is happening under the hood!

## The Three Main Pieces
Imagine your project is like a restaurant:
1. **The Face / The Dining Room (Frontend)**: This is your `index.html`, `style.css`, and `script.js`. It is what the user actually looks at and interacts with.
2. **The Waiter / The Brain (Backend)**: This is your Python `app.py` file using **Flask**. It takes requests from the dining room, goes to the kitchen, and brings the food (data) back.
3. **The Kitchen / The Memory (Database)**: This is **PostgreSQL**. It is basically a giant, highly organized Excel spreadsheet where we store your expenses, categories, and budgets safely so they don't disappear when you close your computer.

---

## 1. How does the Database connect to the Backend?

In your `app.py`, we use a specific Python library called **`psycopg2`**. Think of `psycopg2` as a "translator pipe". 

PostgreSQL only understands a language called **SQL**, while your backend only speaks **Python**. 
In `app.py`, we give this translator pipe the keys to the kitchen (your database username, password, and the name `expense_db`). Whenever your backend needs to save a new expense, it hands Python code to `psycopg2`. The translator turns it into SQL, shoots it down the pipe to PostgreSQL, grabs the results, and hands it back to your Python app.

---

## 2. How is the Backend working?

Your Python backend uses a tool called **Flask**. Flask's entire job is to listen for "HTTP Requests" (which is basically the internet's version of a waiter taking an order).

In `app.py`, you will see lines of code like `@app.route('/api/dashboard_data')`. This is your backend's "Menu". 
When your frontend JavaScript says, *"Hey, I need the numbers to draw the ring chart!"*, it sends a `GET` request to that specific route. 
Flask sees the request, uses the `psycopg2` pipe to ask the database for the sum of all your expenses, packages those numbers into a neat, standardized format called **JSON**, and hands it back to the frontend.

---

## 3. Why are we using Postman?

The ultimate goal of this project is for an **Android App** to automatically read your bank SMS messages and send them directly to your backend without you doing anything. 

However, while you are building and testing on your computer, you don't have that Android app hooked up yet! 
**Postman acts as a "fake Android phone".** 

Postman is a tool that allows developers to manually shoot data at a backend. When you open Postman, paste in a fake $42.50 Uber expense, and hit "Send", it fires a JSON payload directly at your Flask backend's `/api/webhook` route. Your backend has no idea it came from Postman; it just assumes a real bank transaction occurred and saves it!

---

## 4. The Full Flow: What happens where?

Let's walk through the exact journey of a single expense from start to finish:

1. **The Fake Alert (Postman)**: You use Postman to send a $42.50 Uber transaction to your backend.
2. **The Catch (Backend)**: Your `app.py` catches this at the `/api/webhook` route. It uses `psycopg2` to write this expense into your PostgreSQL database. Because it doesn't know what category "Uber" belongs to, it marks the status as `'pending_intervention'`.
3. **The Watcher (Frontend)**: Meanwhile, your browser is open. In `script.js`, there is a hidden loop (`setInterval`) acting as a watchdog. Every 5 seconds, it silently asks the backend: *"Are there any pending transactions?"*
4. **The Modal Pops Up (Frontend)**: Within 5 seconds, the backend responds: *"Yes, we just got a $42.50 Uber ride!"*. Your JavaScript immediately reacts by pausing the dashboard and popping up a large alert box (Modal), forcing you to categorize it.
5. **The Categorization (Frontend -> Backend)**: You select "Transportation" in the dropdown and click "Save". The frontend sends a `PUT` request back to the backend, telling it to update that specific database row with the new category and change the status to `'categorized'`.
6. **The Final Update (Frontend)**: As soon as the save is successful, your frontend asks the backend for the fresh dashboard numbers. The Ring Chart and the Summary Cards instantly update to visually show how that $42.50 affected your overall budget!
# expense-leakage-tracker
