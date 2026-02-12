from app import app, mongo

def update_link():
    with app.app_context():
        # Update slyeee to link to SEOUL-001
        res = mongo.db.users.update_one(
            {'username': 'slyeee'},
            {'$set': {'linked_center_code': 'SEOUL-001'}}
        )
        print(f"Updated slyeee link: Matched {res.matched_count}, Modified {res.modified_count}")
        
        # Ensure Center Exists? Just a placeholder if missing
        if not mongo.db.centers.find_one({'code': 'SEOUL-001'}):
            mongo.db.centers.insert_one({
                'code': 'SEOUL-001',
                'name': '도봉구 정신건강복지센터 (Sync)',
                'region': 'Seoul',
                'description': 'Synced from 150 Backup'
            })
            print("Inserted placeholder center for SEOUL-001")

if __name__ == "__main__":
    update_link()
