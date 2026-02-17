import psycopg2

def force_delete_staff_deep():
    conn = None
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="reboot_db",
            user="slyeee",
            password="",
            port=5432
        )
        cur = conn.cursor()
        
        # 1. Target Staff IDs (Exclude 'slyeee')
        cur.execute("""
            SELECT id FROM users_user 
            WHERE (is_staff = true OR is_superuser = true) 
            AND username != 'slyeee';
        """)
        target_ids = [str(r[0]) for r in cur.fetchall()]
        
        if not target_ids:
            print("No staff to delete.")
            return

        ids_str = ",".join(target_ids)
        print(f"Target Staff IDs: {ids_str}")

        # 2. Delete Dependencies (Deep Cascade)
        # MockInterview -> Portfolio -> User
        
        # Find Portfolios owned by these users
        cur.execute(f"SELECT id FROM career_portfolio WHERE student_id IN ({ids_str});")
        p_ids = [str(r[0]) for r in cur.fetchall()]
        p_ids_str = ",".join(p_ids)
        
        if p_ids:
            print(f"Cleaning MockInterviews for Portfolios: {p_ids_str}")
            cur.execute(f"DELETE FROM career_mockinterview WHERE portfolio_id IN ({p_ids_str});")
            print(f"Deleted {cur.rowcount} mock interviews.")
            
            print(f"Cleaning Portfolios: {p_ids_str}")
            cur.execute(f"DELETE FROM career_portfolio WHERE id IN ({p_ids_str});")
            print(f"Deleted {cur.rowcount} portfolios.")
        
        # Diaries
        print("Cleaning Diaries...")
        cur.execute(f"DELETE FROM diaries WHERE user_id IN ({ids_str});")

        # 3. Delete Users
        print("Deleting Users...")
        cur.execute(f"DELETE FROM users_user WHERE id IN ({ids_str});")
        print(f"SUCCESS: Deleted {cur.rowcount} staff users.")
        
        conn.commit()
        
    except Exception as e:
        print(f"Error: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    force_delete_staff_deep()
