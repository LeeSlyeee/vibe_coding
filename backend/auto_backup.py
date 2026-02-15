
import os
import datetime
import subprocess

def auto_backup():
    try:
        # Create Backup Dir
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # File Name
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f"db_backup_{timestamp}.sql")
        
        # PG Dump Command (Password via env variable)
        # Note: In production, use .pgpass file
        env = os.environ.copy()
        env['PGPASSWORD'] = 'vibe1234'
        
        cmd = [
            'pg_dump',
            '-h', '127.0.0.1',
            '-U', 'vibe_user',
            '-d', 'vibe_db',
            '-f', backup_file
        ]
        
        print(f"📦 Starting DB Backup: {backup_file}")
        
        # Execute
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Backup Successful: {backup_file}")
            
            # Rotate Backups (Keep last 10)
            backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.sql')])
            while len(backups) > 10:
                oldest = backups.pop(0)
                os.remove(oldest)
                print(f"🗑️ Cleaned up old backup: {oldest}")
                
        else:
            print(f"❌ Backup Failed: {result.stderr}")
            if "peer authentication" in result.stderr:
                print("Try setting host explicitly to 127.0.0.1")

    except Exception as e:
        print(f"❌ Backup Error: {e}")

if __name__ == "__main__":
    auto_backup()
