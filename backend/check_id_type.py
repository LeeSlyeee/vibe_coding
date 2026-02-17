import psycopg2

def check_id_type():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="reboot_db",
            user="slyeee",
            password="",
            port=5432
        )
        cur = conn.cursor()
        
        # Check ID column type of users_user
        cur.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users_user' AND column_name = 'id';
        """)
        res = cur.fetchone()
        print(f"ID Column Type: {res[0] if res else 'Not Found'}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_id_type()
