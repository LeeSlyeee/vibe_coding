from app import app, User, Diary, safe_decrypt
import requests
import json

def force_sync_dashboard():
    with app.app_context():
        print("🚀 [Force Sync] Starting manual synchronization to Django Dashboard (8000)...")
        
        # 1. Get All Active Users
        users = User.query.filter(User.center_code != None).all()
        print(f"👥 Found {len(users)} users linked to a center.")

        processed_count = 0
        success_count = 0
        
        for user in users:
            print(f"🧵 Syncing User: {user.username} ({user.nickname}) - Center: {user.center_code}")
            
            # 2. Get All Diaries for User
            diaries = Diary.query.filter_by(user_id=user.id).all()
            print(f"   found {len(diaries)} diaries.")
            
            metrics = []
            for d in diaries:
                processed_count += 1
                try:
                    metrics.append({
                        "created_at": d.created_at.isoformat() if d.created_at else "",
                        "date": d.date,
                        "mood_level": d.mood_level,
                        
                        # Content
                        "event": safe_decrypt(d.event),
                        "emotion": safe_decrypt(d.emotion_desc),
                        "meaning": safe_decrypt(d.emotion_meaning),
                        "selftalk": safe_decrypt(d.self_talk),
                        "sleep": safe_decrypt(d.sleep_condition),
                        "gratitude": safe_decrypt(d.gratitude_note),
                        
                        # AI Data
                        "ai_comment": safe_decrypt(d.ai_comment),
                        "ai_prediction": safe_decrypt(d.ai_emotion),
                        
                        # Rich Data
                        "weather": d.weather,
                        "mode": d.mode,
                        "mood_intensity": d.mood_intensity
                    })
                except Exception as e:
                    print(f"   ⚠️ Skipping diary {d.id} due to error: {e}")
            
            if not metrics:
                print("   ⚠️ No diaries to sync for this user.")
                continue

            # 3. Send Payload to Django
            payload = {
                "center_code": user.center_code,
                "user_nickname": user.nickname or user.username,
                "risk_level": 0, # Default
                "mood_metrics": metrics
            }
            
            try:
                url = "https://217.142.253.35.nip.io/api/v1/centers/sync-data/"
                res = requests.post(url, json=payload, timeout=10, verify=False)
                
                if res.status_code == 200:
                    print(f"   ✅ Sync Success: {res.json()}")
                    success_count += len(metrics)
                else:
                    print(f"   ❌ Sync Failed ({res.status_code}): {res.text}")
            except Exception as e:
                print(f"   ❌ Connection Error: {e}")

        print(f"\n📊 Sync Complete. Processed {processed_count} diaries, Successfully synced {success_count}.")

if __name__ == "__main__":
    force_sync_dashboard()
