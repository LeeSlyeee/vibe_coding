import psycopg2

def delete_professor():
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
        
        target_username = 'professor'
        print(f"Searching for '{target_username}'...")
        
        cur.execute("SELECT id FROM users_user WHERE username = %s;", (target_username,))
        row = cur.fetchone()
        
        if not row:
            print(f"User '{target_username}' not found. Nothing to do.")
            return

        user_id = row[0]
        print(f"Found '{target_username}' with ID: {user_id}")
        
        # Delete Dependencies
        tables_to_clean = [
            'diaries',
            'career_portfolio',
            'learning_dailyquiz',
            'learning_quizattempt',
            'learning_learningsession',
            'learning_lecture_students',
            'learning_studentchecklist'
        ]
        
        for table in tables_to_clean:
            # Check if table exists first to avoid errors
            cur.execute("SELECT to_regclass(%s);", (table,))
            if cur.fetchone()[0]:
                print(f"Cleaning {table}...")
                try:
                    # Most tables use 'user_id' or 'student_id'
                    col_name = 'user_id' if table in ['diaries', 'learning_lecture_students'] else 'student_id'
                    cur.execute(f"DELETE FROM {table} WHERE {col_name} = %s;", (user_id,))
                    print(f"  Deleted {cur.rowcount} rows.")
                except Exception as e:
                    print(f"  Warning: Failed to clean {table} ({e})")
                    conn.rollback()
        
        # Delete User
        print(f"Deleting user '{target_username}'...")
        cur.execute("DELETE FROM users_user WHERE id = %s;", (user_id,))
        print(f"SUCCESS: Deleted user '{target_username}'.")
        
        conn.commit()
        
    except Exception as e:
        print(f"Error: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    delete_professor()
