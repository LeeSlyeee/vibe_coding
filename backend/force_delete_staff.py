import psycopg2

def force_delete_staff():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="reboot_db",
            user="slyeee",
            password="",
            port=5432
        )
        cur = conn.cursor()
        
        # 1. First, identify target IDs to delete (Staff/Superuser excluding self)
        cur.execute("""
            SELECT id FROM users_user 
            WHERE (is_staff = true OR is_superuser = true) 
            AND username != 'slyeee';
        """)
        target_ids = [str(r[0]) for r in cur.fetchall()]
        
        if target_ids:
            ids_str = ",".join(target_ids)
            print(f"Target IDs for deletion: {ids_str}")

            # 2. Delete Dependencies (Cascade Logic Manual)
            # CareerPortfolio?
            print("--- Cleaning dependencies ---")
            try:
                cur.execute(f"DELETE FROM career_portfolio WHERE student_id IN ({ids_str});")
                print(f"Deleted {cur.rowcount} from career_portfolio")
            except Exception as e:
                print(f"Warning: career_portfolio delete failed: {e}")
                conn.rollback()

            # Diaries? (If any staff wrote diaries)
            try:
                cur.execute(f"DELETE FROM diaries WHERE user_id IN ({ids_str});")
                print(f"Deleted {cur.rowcount} from diaries")
            except Exception as e:
                print(f"Warning: diaries delete failed: {e}")
                conn.rollback()
                
            # 3. Delete Users
            print("--- Deleting Users ---")
            cur.execute(f"DELETE FROM users_user WHERE id IN ({ids_str});")
            print(f"SUCCESS: Deleted {cur.rowcount} staff users.")
            
        else:
            print("No staff to delete.")
            
        # 4. Promote 'slyeee'
        print("--- Promoting 'slyeee' ---")
        cur.execute("""
            UPDATE users_user 
            SET is_staff = true, 
                is_superuser = true,
                role = 'admin' 
            WHERE username = 'slyeee';
        """)
        print("User 'slyeee' is now Admin.")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    force_delete_staff()
