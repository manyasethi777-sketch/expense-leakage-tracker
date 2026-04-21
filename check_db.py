import psycopg2
conn = psycopg2.connect(host='localhost', database='expense_db', user='postgres', password='agrim2510')
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name ILIKE 'categories'")
print(cur.fetchall())
