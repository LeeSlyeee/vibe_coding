import psycopg2

def check_reboot_db():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="reboot_db",
            user="slyeee",
            password=""
        )
        cur = conn.cursor()
        
        # Check Users (Reboot Project Table)
        try:
            cur.execute("SELECT count(*) FROM users_user;")
            u_count = cur.fetchone()[0]
            print(f"PostgreSQL (reboot_db) 'users_user' count: {u_count}")
        except Exception as e:
            print(f"Could not count users_user: {e}")
            u_count = 0

        # Check Diaries (Haru-On Table)
        try:
            cur.execute("SELECT count(*) FROM diaries;")
            d_count = cur.fetchone()[0]
            print(f"PostgreSQL (reboot_db) 'diaries' count: {d_count}")
        except Exception as e:
            print(f"Could not count diaries (Table likely missing): {e}")
            d_count = 0
            
        conn.close()
        
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    check_reboot_db()
