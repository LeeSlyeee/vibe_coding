from app import app, db, User
from werkzeug.security import generate_password_hash

def reset_password(username, new_password):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"User found: {user.username}")
            # Generate new hash
            hashed_pw = generate_password_hash(new_password)
            print(f"Generated Hash: {hashed_pw}")
            
            user.password = hashed_pw
            db.session.commit()
            print(f"Password for '{username}' has been reset successfully.")
        else:
            print(f"User '{username}' not found.")

if __name__ == "__main__":
    # Resetting password for 'slyeee' to 'mechin12qw!!'
    reset_password('slyeee', 'mechin12qw!!')
