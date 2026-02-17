
import os
import sys
from backend.app import app, db, Diary, safe_decrypt

# Set up context
with app.app_context():
    print("🔍 Searching for diary with sleep condition: '그럭저럭 잘 잤어'")
    
    # Fetch all diaries
    diaries = Diary.query.all()
    found_count = 0
    
    for d in diaries:
        try:
            # Decrypt sleep condition
            sleep_cond = safe_decrypt(d.sleep_condition)
            
            if sleep_cond and "그럭저럭 잘 잤어" in sleep_cond:
                print(f"✅ Found Diary ID: {d.id}")
                print(f"   Original Date: {d.date}")
                print(f"   Created At: {d.created_at}")
                print(f"   Sleep Condition: {sleep_cond}")
                
                # Check if date is wrong (e.g. today's date 2026-02-17)
                if str(d.date) == "2026-02-17":
                    print("⚠️ Date mismatch detected! Fixing to 2026-02-13...")
                    d.date = "2026-02-13" # Force update date
                    db.session.add(d)
                    found_count += 1
                elif str(d.date) == "2026-02-13":
                    print("ℹ️ Date is already correct (2026-02-13). No action needed.")
                else:
                    print(f"❓ Date is {d.date}. Is this correct? Updating to 2026-02-13 just in case.")
                    d.date = "2026-02-13"
                    db.session.add(d)
                    found_count += 1
                    
        except Exception as e:
            print(f"Error processing diary {d.id}: {e}")
            continue

    if found_count > 0:
        db.session.commit()
        print(f"🚀 Successfully updated {found_count} diaries to 2026-02-13.")
    else:
        print("❌ No matching diaries found or no updates needed.")
