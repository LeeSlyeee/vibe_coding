
from app import app, db
from models import User
from werkzeug.security import generate_password_hash, check_password_hash

def reset_slyeee_password():
    print("🔄 Resetting password for 'slyeee'...")
    
    with app.app_context():
        user = User.query.filter_by(username='slyeee').first()
        if not user:
            print("❌ User 'slyeee' not found in PostgreSQL!")
            return

        new_password = "1234"
        hashed_pw = generate_password_hash(new_password)
        
        user.password_hash = hashed_pw
        db.session.commit()
        
        print(f"✅ Password for '{user.username}' has been reset to '{new_password}'.")
        
        # Verify
        if check_password_hash(user.password_hash, new_password):
            print("✅ Password hash verification passed.")
        else:
            print("❌ Password hash verification FAILED!")

if __name__ == "__main__":
    reset_slyeee_password()
