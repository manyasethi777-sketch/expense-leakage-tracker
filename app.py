import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Database connection details
DB_HOST = "localhost"
DB_NAME = "expense_db"
DB_USER = "postgres"
DB_PASS = "agrim2510"

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT category_id, category_name AS name FROM Categories ORDER BY category_name;")
        categories = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"categories": categories}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pending_intervention', methods=['GET'])
def get_pending_intervention():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT expense_id, amount, description, source, expense_date 
            FROM Expenses 
            WHERE status = 'pending_intervention' 
            ORDER BY expense_date ASC, expense_id ASC 
            LIMIT 1;
        """
        cur.execute(query)
        pending = cur.fetchone()
        cur.close()
        conn.close()
        
        if pending:
            return jsonify({"status": "found", "transaction": pending}), 200
        else:
            return jsonify({"status": "not_found"}), 200
            
    except Exception as e:
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
        
        query = """
            UPDATE Expenses 
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
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leakage', methods=['GET'])
def get_leakage():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Calculate total wasted money (is_essential = false)
        query = """
            SELECT COALESCE(SUM(e.amount), 0) AS total_wasted
            FROM Expenses e
            JOIN Categories c ON e.category_id = c.category_id
            WHERE c.is_essential = false;
        """
        cur.execute(query)
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return jsonify({"total_wasted": result['total_wasted']}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/webhook/bank_transaction', methods=['POST'])
def bank_transaction_webhook():
    try:
        data = request.get_json()
        
        if not data or 'amount' not in data or 'source' not in data:
            return jsonify({"error": "Missing 'amount' or 'source' in request body"}), 400
            
        amount = data['amount']
        source = data['source']
        
        # Default placeholder values per requirements
        user_id = 1
        category_id = 1
        status = 'pending_intervention'
        
        # Populate other schema fields
        description = data.get('description', 'Bank transaction webhook input')
        expense_date = datetime.now().date()
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            INSERT INTO expenses 
            (amount, description, expense_date, source, user_id, category_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING expense_id;
        """
        
        cur.execute(query, (amount, description, expense_date, source, user_id, category_id, status))
        new_expense_id = cur.fetchone()['expense_id']
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "message": "Expense created successfully", 
            "expense_id": new_expense_id, 
            "status": "pending_intervention"
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
