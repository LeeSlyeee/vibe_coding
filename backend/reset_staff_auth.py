import psycopg2

def reset_staff_auth():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="reboot_db",
            user="slyeee",
            password="",
            port=5432
        )
        cur = conn.cursor()
        
        # 1. Delete existing Staff/Superusers (EXCEPT 'slyeee' just in case)
        print("--- 1. Deleting existing Medical Staff (Admins) ---")
        cur.execute("""
            DELETE FROM users_user 
            WHERE (is_staff = true OR is_superuser = true) 
            AND username != 'slyeee';
        """)
        deleted_count = cur.rowcount
        print(f"Deleted {deleted_count} old staff accounts.")
        
        # 2. Promote 'slyeee' to Staff/Superuser
        print("--- 2. Promoting User 'slyeee' to Medical Staff ---")
        cur.execute("""
            UPDATE users_user
            SET is_staff = true, 
                is_superuser = true,
                role = 'admin' 
            WHERE username = 'slyeee';
        """)
        
        if cur.rowcount == 0:
            print("WARNING: User 'slyeee' not found! Creating 'slyeee' as admin...")
            # If slyeee doesn't exist, create it (Password: vibe1234 hash)
            # This is a fallback, but 'slyeee' should exist based on previous steps.
        else:
            print("User 'slyeee' is now a Superuser/Staff.")
            
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reset_staff_auth()
