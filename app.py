import multiprocessing
import os
from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)    

def get_db_connection():  
    return mysql.connector.connect(
        host="127.0.0.1",
        port=8889,
        user="root",
        password="root", 
        database="expense_tracker",
        autocommit=True,
        connection_timeout=60
    )

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
       
        cur.execute("SELECT category_id, category_name AS name FROM categories ORDER BY category_name;")
        categories = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"categories": categories}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/pending_intervention', methods=['GET'])
def get_pending_intervention():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        
        query = """
            SELECT expense_id, amount, description, source, expense_date
            FROM expenses
            WHERE status = 'pending_intervention'
            ORDER BY expense_date ASC, expense_id ASC
            LIMIT 1;
        """
        cur.execute(query)
        pending = cur.fetchone()
        cur.close()
        conn.close()

        if pending:
            if pending.get('expense_date'):
                pending['expense_date'] = pending['expense_date'].strftime('%Y-%m-%d')
            return jsonify({"status": "found", "transaction": pending}), 200
        else:
            return jsonify({"status": "not_found"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/expenses/<int:expense_id>/categorize', methods=['PUT'])
def categorize_expense(expense_id):
    try:
        data = request.get_json()
        if not data or 'category_id' not in data:
            return jsonify({"error": "Missing 'category_id'"}), 400

        category_id = data['category_id']
        conn = get_db_connection()
        cur = conn.cursor()

        # Updated 'id' to 'expense_id'
        query = """
            UPDATE expenses
            SET category_id = %s, status = 'categorized'
            WHERE expense_id = %s AND status = 'pending_intervention';
        """
        cur.execute(query, (category_id, expense_id))

        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({"error": "Expense not found or already categorized"}), 404

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Expense categorized successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/dashboard_data', methods=['GET'])
def get_dashboard_data():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # 1. Fetch monthly limit from user_settings (Replaces budgets table)
        cur.execute("""
            SELECT monthly_limit FROM user_settings
            WHERE user_id = 1
            LIMIT 1;
        """)
        settings = cur.fetchone()
        budget_limit = float(settings['monthly_limit']) if settings and settings['monthly_limit'] else 0

        # 2. Fetch total spent and total wasted
        query_totals = """
            SELECT
                COALESCE(SUM(e.amount), 0) AS total_spent,
                COALESCE(SUM(CASE WHEN c.is_essential = 0 THEN e.amount ELSE 0 END), 0) AS total_wasted
            FROM expenses e
            JOIN categories c ON e.category_id = c.category_id
            WHERE e.user_id = 1 AND e.status = 'categorized';
        """
        cur.execute(query_totals)
        totals = cur.fetchone()

        # 3. Fetch all categorized expenses
        query_expenses = """
            SELECT
                e.expense_id, e.amount, e.description,
                e.expense_date AS date,
                c.category_name, c.is_essential
            FROM expenses e
            JOIN categories c ON e.category_id = c.category_id
            WHERE e.user_id = 1 AND e.status = 'categorized'
            ORDER BY e.expense_date DESC, e.expense_id DESC;
        """
        cur.execute(query_expenses)
        all_expenses = cur.fetchall()

        cur.close()
        conn.close()

        for exp in all_expenses:
            if exp.get('date'):
                exp['date'] = exp['date'].strftime('%Y-%m-%d')

        return jsonify({
            "budget_limit": budget_limit,
            "total_spent": float(totals['total_spent']),
            "total_wasted": float(totals['total_wasted']),
            "all_expenses": all_expenses
        }), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/budget', methods=['PUT'])
def update_budget():
    try:
        data = request.json
        new_limit = data.get('monthly_limit')
        if new_limit is None:
            return jsonify({"error": "monthly_limit is required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Update existing user_settings instead of budgets
        cur.execute("""
            UPDATE user_settings SET monthly_limit = %s
            WHERE user_id = 1
        """, (new_limit,))

        if cur.rowcount == 0:
            # Insert new row if user_settings doesn't exist
            cur.execute("""
                INSERT INTO user_settings (user_id, monthly_limit)
                VALUES (1, %s)
            """, (new_limit,))

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Budget updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("""
            SELECT message, created_at 
            FROM alerts 
            WHERE user_id = 1 
            ORDER BY created_at DESC 
            LIMIT 10;
        """)
        alerts = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Format the dates for the frontend
        for alert in alerts:
            if alert.get('created_at'):
                alert['created_at'] = alert['created_at'].strftime('%Y-%m-%d %H:%M')
                
        return jsonify({"alerts": alerts}), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/api/expenses', methods=['DELETE'])
def reset_expenses():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Deletes all expenses for the default user
        cur.execute("DELETE FROM expenses WHERE user_id = 1;")
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "All expenses reset successfully"}), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/webhook/bank_transaction', methods=['POST'])
def bank_transaction_webhook():
    try:
        data = request.get_json()

        if not data or 'amount' not in data or 'source' not in data:
            return jsonify({"error": "Missing 'amount' or 'source' in request body"}), 400

        amount = data['amount']
        source = data['source']
        description = data.get('description', 'Bank transaction webhook input')
        expense_date = datetime.now().date()

        user_id = 1
        category_id = 1
        status = 'pending_intervention'

        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Insert the Expense
        query = """
            INSERT INTO expenses
            (amount, description, expense_date, source, user_id, category_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        cur.execute(query, (amount, description, expense_date, source, user_id, category_id, status))
        new_expense_id = cur.lastrowid

        # 2. Insert the Alert (This fixes the Pylance warning!)
        query_alert = """
            INSERT INTO alerts (user_id, message, created_at) 
            VALUES (1, %s, %s);
        """
        # Create a dynamic message for the alert
        alert_msg = f"Action Required: Uncategorized transaction from {source} for ₹{amount}."
        cur.execute(query_alert, (alert_msg, datetime.now()))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "message": "Expense and alert created successfully",
            "expense_id": new_expense_id,
            "status": "pending_intervention"
        }), 201

    except Error as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
