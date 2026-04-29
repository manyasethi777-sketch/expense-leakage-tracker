import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    database='expense_tracker',
    user='root',        # change if needed
    password='',        # change if needed
    port=3306           # MAMP default is 8889, XAMPP is 3306
)

cur = conn.cursor()
cur.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'categories' AND TABLE_SCHEMA = 'expense_tracker'")
print(cur.fetchall())

cur.close()
conn.close()
