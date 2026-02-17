
from app import app, db
from models import User
from werkzeug.security import generate_password_hash, check_password_hash

def reset_slyeee_password_v2():
    print("🔄 Resetting password for 'slyeee' (Attempt 2 - Correct Field)...")
    
    with app.app_context():
        # 1. Get User
        user = User.query.filter_by(username='slyeee').first()
        if not user:
            print("❌ User 'slyeee' not found in PostgreSQL!")
            return

        print(f"👤 Found User: {user.username} (ID: {user.id})")
        print(f"🔒 Current Password Hash (Before): {user.password[:20]}...")

        # 2. Reset Password
        new_password = "1234"
        # Generate hash with method 'pbkdf2:sha256' compatible with Werkzeug
        hashed_pw = generate_password_hash(new_password)
        
        # CORRECT FIELD: 'password', NOT 'password_hash'
        user.password = hashed_pw 
        
        db.session.add(user) # Dirty check
        db.session.commit()
        
        # 3. Verify Persistence
        # Re-fetch from DB to be sure
        db.session.expire(user) 
        refetched_user = User.query.get(user.id)
        
        print(f"🔒 New Password Hash (After): {refetched_user.password[:20]}...")
        
        if check_password_hash(refetched_user.password, new_password):
            print(f"✅ Password SUCCESSFULLY reset to '{new_password}'.")
        else:
            print("❌ Password verification FAILED after fetch!")

if __name__ == "__main__":
    reset_slyeee_password_v2()
