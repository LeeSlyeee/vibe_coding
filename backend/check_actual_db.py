from pymongo import MongoClient

def check():
    uri = "mongodb://localhost:27017" # Default
    client = MongoClient(uri)
    
    candidates = ["mood_diary", "maumon_db", "mood_diary_db"]
    
    print("--- MONGO DB SEARCH ---")
    
    for db_name in candidates:
        db = client[db_name]
        try:
            u_count = db.users.count_documents({})
            d_count = db.diaries.count_documents({})
            m_count = db.member.count_documents({}) # Legacy check
            di_count = db.diary.count_documents({}) # Legacy check
            
            print(f"[{db_name}]")
            print(f"  - users: {u_count}")
            print(f"  - diaries: {d_count}")
            print(f"  - member (legacy): {m_count}")
            print(f"  - diary (legacy): {di_count}")
            
            if u_count > 0 or d_count > 0:
                print(f"  ==> POSSIBLE TARGET DB!")
        except Exception as e:
            print(f"[{db_name}] Error: {e}")
            
    print("--- END ---")

if __name__ == "__main__":
    check()
