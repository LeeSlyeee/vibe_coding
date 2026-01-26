from app import mongo, app
from werkzeug.security import generate_password_hash

def reset_password():
    with app.app_context():
        # Find user
        user = mongo.db.users.find_one({'username': 'severe_test'})
        if user:
            # Update password
            new_hash = generate_password_hash('12qw')
            mongo.db.users.update_one(
                {'username': 'severe_test'},
                {'$set': {'password': new_hash}}
            )
            print(f"✅ Password for 'severe_test' has been reset to '12qw'")
        else:
            print("❌ User 'severe_test' not found")

if __name__ == "__main__":
    reset_password()
