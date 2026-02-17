import psycopg2

def switch_roles():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="reboot_db",
            user="slyeee",
            password="",
            port=5432
        )
        cur = conn.cursor()
        
        print("--- Switching Roles ---")
        
        # 1. Demote 'slyeee' to Patient
        print("1. Demoting 'slyeee' to Patient...")
        cur.execute("""
            UPDATE users_user 
            SET is_staff = false, 
                is_superuser = false,
                role = 'student'  -- Assuming 'student' or 'member' is the patient role
            WHERE username = 'slyeee';
        """)
        
        # 2. Promote 'professor' to Medical Staff
        print("2. Promoting 'professor' to Medical Staff...")
        cur.execute("""
            UPDATE users_user 
            SET is_staff = true, 
                is_superuser = true,
                role = 'admin' 
            WHERE username = 'professor';
        """)
        
        if cur.rowcount == 0:
            print("WARNING: User 'professor' not found! Please create it first.")
            
        conn.commit()
        print("SUCCESS: Roles Switched.")
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    switch_roles()
