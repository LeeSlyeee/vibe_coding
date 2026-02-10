import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv('DB_HOST', '127.0.0.1')
user = os.getenv('DB_USER', 'root')
password = os.getenv('DB_PASSWORD', '')
port = int(os.getenv('DB_PORT', 3306))
db_name = os.getenv('DB_NAME', 'maumon_db')

try:
    conn = pymysql.connect(host=host, user=user, password=password, port=port)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print(f"Database '{db_name}' created or already exists.")
    conn.close()
except Exception as e:
    print(f"Error creating database: {e}")
