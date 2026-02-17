import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Flask DB Credentials (Known Working)
DB_HOST = "127.0.0.1"
DB_NAME = "vibe_db"
DB_USER = "vibe_user"
DB_PASS = "vibe1234"

def fix_auth():
    try:
        # Connect to 'postgres' or 'vibe_db' as vibe_user
        print(f"🔌 Connecting as {DB_USER}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # 1. Try to Reset Password for maumON_admin
        try:
            print("🔑 Attempting to reset password for maumON_admin...")
            cur.execute("ALTER USER \"maumON_admin\" WITH PASSWORD 'maumON_1234';")
            print("✅ Password reset successful!")
        except Exception as e:
            print(f"❌ Password reset failed: {e}")
            
        # 2. Try to Grant Permissions to vibe_user for reboot_db (Backup plan)
        try:
            print("🛡️ Attempting to GRANT ALL on reboot_db to vibe_user...")
            cur.execute("GRANT ALL PRIVILEGES ON DATABASE reboot_db TO vibe_user;")
            print("✅ Database Grant successful!")
        except Exception as e:
            print(f"❌ Database Grant failed: {e}")

        conn.close()
        
        # 3. Connect to reboot_db directly and grant table permissions
        print("\n🔌 Connecting to reboot_db as vibe_user...")
        conn2 = psycopg2.connect(
            host=DB_HOST,
            database="reboot_db",
            user=DB_USER,
            password=DB_PASS
        )
        conn2.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur2 = conn2.cursor()
        
        try:
            print("📑 Granting table permissions...")
            cur2.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO vibe_user;")
            cur2.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO vibe_user;")
            cur2.execute("GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO vibe_user;")
            print("✅ Table permissions granted!")
        except Exception as e:
            print(f"❌ Table permission grant failed: {e}")
            
        conn2.close()

    except Exception as e:
        print(f"🔥 Critical Fatal Error: {e}")

if __name__ == "__main__":
    fix_auth()
