import psycopg2

def inspect_users_detailed():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="reboot_db",
            user="slyeee",
            password="",
            port=5432
        )
        cur = conn.cursor()
        
        print("--- Inspecting Users Detailed ---")
        cur.execute("SELECT id, username, is_staff, is_superuser, is_active FROM users_user;")
        rows = cur.fetchall()
        
        print(f"{'ID':<5} {'Username':<20} {'Staff':<6} {'Super':<6} {'Active':<6}")
        print("-" * 60)
        for r in rows:
            # PostgreSQL boolean returns True/False
            print(f"{r[0]:<5} {r[1]:<20} {str(r[2]):<6} {str(r[3]):<6} {str(r[4]):<6}")
            
        print("\n--- Counting Candidates ---")
        count = 0
        for r in rows:
            u, is_staff, is_super, is_active = r[1], r[2], r[3], r[4]
            # Logic in staff_views.py: is_staff=False, exclude app_
            if not is_staff and not u.startswith('app_'): 
                print(f"User '{u}' matches criteria.")
                count += 1
            else:
                print(f"User '{u}' excluded.")
                
        print(f"Expected Count based on DB: {count}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_users_detailed()
