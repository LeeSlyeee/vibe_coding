import psycopg2
import os

def check_local_postgres():
    # Candidates
    users = ["slyeee", "postgres", "root"]
    dbs = ["postgres", "reboot_db", "vibe_db", "mood_diary_db", "haruon_db"]
    
    found_target = False
    
    print("--- START DISCOVERY ---")
    
    for user in users:
        for db in dbs:
            try:
                # Try connecting without password (local trust) or default
                conn = psycopg2.connect(
                    host="127.0.0.1",
                    database=db,
                    user=user,
                    password="", # Try empty first
                    connect_timeout=3
                )
                
                cur = conn.cursor()
                
                # Check Tables
                try:
                    cur.execute("SELECT count(*) FROM users;")
                    u_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT count(*) FROM diaries;")
                    d_count = cur.fetchone()[0]
                    
                    print(f"[SUCCESS] User='{user}', DB='{db}'")
                    print(f"   -> Users: {u_count}, Diaries: {d_count}")
                    
                    if u_count == 2 and d_count == 15:
                        print("   !!! MATCH FOUND (2 Users, 15 Diaries) !!!")
                        found_target = True
                        
                except Exception as e:
                    print(f"[CONNECTED but Error] User='{user}', DB='{db}' -> {e}")
                    
                conn.close()
                
            except Exception as e:
                # print(f"[Valid Failed] {user}@{db}")
                pass
                
    print("--- END DISCOVERY ---")

if __name__ == "__main__":
    check_local_postgres()
