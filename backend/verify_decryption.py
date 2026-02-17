
from app import app, db, crypto
from models import User, Diary

def verify_decryption():
    print("🔐 Verifying Decryption for 'slyeee'...")
    
    if not crypto:
        print("❌ Crypto Manager is NULL!")
        return

    with app.app_context():
        user = User.query.filter_by(username='slyeee').first()
        if not user:
            print("❌ User not found")
            return
            
        diary = Diary.query.filter_by(user_id=user.id).first()
        if not diary:
            print("❌ No diary found")
            return
            
        print(f"📄 Testing Diary ID: {diary.id}")
        content = diary.event
        print(f"🔒 Ciphertext: {content[:30]}...")
        
        try:
            decrypted = crypto.decrypt(content)
            print(f"✅ Decryption SUCCESS! Result: {decrypted[:50]}...")
        except Exception as e:
            print(f"❌ Decryption FAILED: {e}")
            print("⚠️ The Encryption Key currently in use CANNOT decrypt this data.")

if __name__ == "__main__":
    verify_decryption()
