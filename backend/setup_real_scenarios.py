import sys
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add backend directory to path to import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, mongo

def setup_user_scenarios():
    with app.app_context():
        print("🚀 Setting up Real User Scenarios...")

        # 1. Cleanup specific test users
        usernames = ['web_patient', 'ios_guardian_account', 'ios_patient_account', 'web_guardian']
        mongo.db.users.delete_many({'username': {'$in': usernames}})
        mongo.db.share_codes.delete_many({'user_id': {'$in': usernames}}) # Needs ID check later
        # Note: share_relationships cleanup requires IDs, will do after creation
        
        # --- Scenario A: Web Patient (D-Day) -> iOS Guardian ---
        # Web User: 'web_patient' (Birthday: Today!) -> To trigger "Based on Today" badge
        today = datetime.now()
        birthday_today = f"1995-{today.month:02d}-{today.day:02d}"
        
        web_patient_id = mongo.db.users.insert_one({
            'username': 'web_patient',
            'password_hash': generate_password_hash('test1234', method='pbkdf2:sha256'),
            'nickname': '웹_오늘생일', # Intended to show "Today Birthday" badge on iOS
            'birth_date': birthday_today, 
            'role': 'patient',
            'created_at': datetime.now()
        }).inserted_id
        print(f"✅ Created 'web_patient' (Birthday: {birthday_today} - TODAY!)")

        # iOS User (Guardian): 'ios_guardian_account'
        ios_guardian_id = mongo.db.users.insert_one({
            'username': 'ios_guardian_account',
            'password_hash': generate_password_hash('test1234', method='pbkdf2:sha256'),
            'nickname': 'iOS_보호자',
            'role': 'guardian',
            'created_at': datetime.now()
        }).inserted_id
        print(f"✅ Created 'ios_guardian_account'")


        # --- Scenario B: iOS Patient (D-Day Upcoming) -> Web Guardian ---
        # iOS User (Patient): 'ios_patient_account' (Birthday: D-3)
        birthday_d3 = today + timedelta(days=3)
        birthday_d3_str = f"1998-{birthday_d3.month:02d}-{birthday_d3.day:02d}"

        ios_patient_id = mongo.db.users.insert_one({
            'username': 'ios_patient_account',
            'password_hash': generate_password_hash('test1234', method='pbkdf2:sha256'),
            'nickname': 'iOS_내담자_D3',
            'birth_date': birthday_d3_str,
            'role': 'patient',
            'created_at': datetime.now()
        }).inserted_id
        print(f"✅ Created 'ios_patient_account' (Birthday: {birthday_d3_str} - D-3)")

        # Web User (Guardian): 'web_guardian'
        web_guardian_id = mongo.db.users.insert_one({
            'username': 'web_guardian',
            'password_hash': generate_password_hash('test1234', method='pbkdf2:sha256'),
            'nickname': '웹_보호자',
            'role': 'guardian',
            'created_at': datetime.now()
        }).inserted_id
        print(f"✅ Created 'web_guardian'")
        
        # Cleanup Relationships for these new IDs
        ids = [web_patient_id, ios_guardian_id, ios_patient_id, web_guardian_id]
        mongo.db.share_relationships.delete_many({
            '$or': [{'sharer_id': {'$in': ids}}, {'viewer_id': {'$in': ids}}]
        })
        
        print("\n✨ All Accounts Ready!")
        print("---------------------------------------------------")
        print("[Scenario 1] Verify 'Today Birthday' Badge on iOS")
        print("1. Log in to iOS App with: ios_guardian_account / test1234")
        print("2. Log in to Web with: web_patient / test1234")
        print("3. Generate code on Web -> Input code on iOS")
        print("---------------------------------------------------")
        print("[Scenario 2] Verify 'D-3' Badge on Web")
        print("1. Log in to iOS App with: ios_patient_account / test1234")
        print("2. Log in to Web with: web_guardian / test1234")
        print("3. Generate code on iOS -> Input code on Web")
        print("---------------------------------------------------")

if __name__ == '__main__':
    try:
        setup_user_scenarios()
    except Exception as e:
        print(f"💥 Error: {e}")
