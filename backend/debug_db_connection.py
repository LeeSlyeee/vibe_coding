import pymysql
import sys

print(f"Python connecting to: 127.0.0.1:3306 User: root")

try:
    connection = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='1q2w3e4r',
        database='mood_diary',
        charset='utf8mb4'
    )
    
    with connection.cursor() as cursor:
        # 1. Server Version
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()
        print(f"Connected to MariaDB Version: {version[0] if version else 'Unknown'}")
        
        # 2. Connection ID
        cursor.execute("SELECT CONNECTION_ID();")
        conn_id = cursor.fetchone()
        print(f"Current Connection ID: {conn_id[0] if conn_id else 'Unknown'}")
        
        # 3. List Tables
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("\n[ Tables in 'mood_diary' ]")
        if not tables:
            print("  (No tables found)")
        for table in tables:
            print(f"  - {table[0]}")

except Exception as e:
    print(f"\n[!] Connection Failed: {e}")
