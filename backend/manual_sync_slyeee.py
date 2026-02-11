import requests
import json
from app import app, mongo
from b2g_routes import INSIGHT_MIND_URL
from datetime import datetime

username = "slyeee"
# Password is unknown to me.
# But I can access hashed password in DB?
# No, I need PLAIN password to login to 150.
# I DON'T HAVE SLYEEE PASSWORD.
# I cannot run manual sync without password.

# Alternative: Login as slyeee using 'user_39ca9a' password?
# If Hijack works, then passwords match.
# If I can verify passwords match?
# I can try to login to 150 using 'user_39ca9a' plain password?
# I DON'T HAVE PLAIN PASSWORD.
# Passwords are hashed.

# WAIT.
# The App sends Plain Password to /api/login.
# If logs worked, I could see it? No, logs shouldn't print passwords.
# Flask receives it.
# Hijack logic checks it against hash.

# Plan B:
# I cannot trigger Sync externally without password.
# But I can DEBUG the Sync Thread logic by adding logging TO A FILE inside the thread.
# Explicit File Write.

def debug_log(msg):
    with open("/home/ubuntu/sync_debug.txt", "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

# Use this in b2g_routes.py?
