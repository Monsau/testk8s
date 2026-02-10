import psycopg2

conn = psycopg2.connect(
    host='192.168.8.50', port=30432,
    database='demo', user='postgres', password='admin123'
)
cur = conn.cursor()

# Lister les tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = cur.fetchall()
print("Tables existantes:", tables if tables else "(aucune)")

# Lister les bases de données
cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
dbs = cur.fetchall()
print("Bases de données:", dbs)

conn.close()
