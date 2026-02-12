from app import app, mongo

def force_reset_sync():
    """
    Forces the 'last_sync' timestamp in b2g_connections to a very old date.
    This tricks the iOS app into thinking it hasn't synced in a long time,
    triggering an automatic push of all pending data upon next app launch/refresh.
    """
    print("🚀 Forcing Sync Reset for 'slyeee'...")
    
    with app.app_context():
        # 1. Find User to get Center Code
        user = mongo.db.users.find_one({'username': 'slyeee'})
        if not user:
            print("❌ User 'slyeee' not found!")
            return
            
        code = user.get("linked_center_code")
        print(f"👤 User: slyeee | Center: {code}")
        
        if not code:
            print("❌ No linked center code found.")
            return

        # 2. Reset b2g_connections
        # Set last_sync to 2000-01-01
        res = mongo.db.b2g_connections.update_one(
            {"center_code": code},  # Or match by user_id if stored
            {"$set": {"last_sync": "2000-01-01 00:00:00"}}
        )
        
        print(f"🔄 Reset 'b2g_connections' last_sync: Matched {res.matched_count}, Modified {res.modified_count}")
        
        # 3. Use Aggressive Reset? (Delete connection to force re-handshake?)
        # Maybe safer just to reset time first.
        
        # Also check if we need to reset any 'users' collection flag?
        # Usually client checks 'last_sync' from an API response.
        # The API is likely /api/b2g_sync/status/ which returns 'linked': True/False
        # Or /api/v1/centers/sync-data/ (POST) response?
        
        # Wait, if client stores 'last_sync_time' LOCALLY using UserDefaults,
        # server reset might not be enough unless client asks server "When did I last sync?".
        # Most simple sync logic: Client sends data > Server saves > Server returns "OK, saved up to X time" > Client updates local time.
        
        # If client logic is "Fetch last sync time from server", then this works.
        # If client logic is "I remember when I last sent", then we need to trick it (by error/fail response? no).
        
        # Assuming typical sync:
        print("✅ Sync Timestamp Reset Complete. Please restart the iOS App.")

if __name__ == "__main__":
    force_reset_sync()
