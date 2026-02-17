import psycopg2

def inspect_users():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="reboot_db",
            user="slyeee",
            password="",
            port=5432
        )
        cur = conn.cursor()
        
        print("--- Inspecting Users in 'users_user' ---")
        cur.execute("SELECT id, username, is_staff, is_superuser FROM users_user;")
        rows = cur.fetchall()
        
        print(f"{'ID':<5} {'Username':<20} {'Is Staff':<10} {'Is Superuser':<15}")
        print("-" * 55)
        for r in rows:
            print(f"{r[0]:<5} {r[1]:<20} {r[2]:<10} {r[3]:<15}")
            
        print("\n--- Dashboard Logic Simulation ---")
        # Logic: is_staff=False, is_superuser=False, exclude app_
        staff_count = 0
        patient_count = 0
        
        for r in rows:
            username = r[1]
            is_staff = r[2]
            is_surper = r[3]
            
            if is_staff or is_surper:
                print(f"User '{username}' -> EXCLUDED (Staff/Superuser)")
                staff_count += 1
            elif username.startswith('app_'):
                print(f"User '{username}' -> EXCLUDED (System Account via app_ prefix)")
            else:
                print(f"User '{username}' -> INCLUDED as Patient")
                patient_count += 1
                
        print(f"\nResult: Staff={staff_count}, Patients={patient_count}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_users()
