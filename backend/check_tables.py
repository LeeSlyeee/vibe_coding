import pymysql

connection = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='1q2w3e4r',
    database='mood_diary',
    charset='utf8mb4'
)

try:
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("Existing tables:", tables)
finally:
    connection.close()
