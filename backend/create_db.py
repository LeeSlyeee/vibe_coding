import pymysql

# Note: Connecting to default 'mysql' database to create the new one
connection = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='1q2w3e4r',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with connection.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS mood_diary CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print("Database 'mood_diary' created or verified successfully.")
finally:
    connection.close()
