
from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient("mongodb://localhost:27017/")
db = client['mood_diary_db']

target_ids = [
    ObjectId('69716983d4e7ae84925e62eb'),
    ObjectId('69716983d4e7ae84925e62ec'),
    ObjectId('69716983d4e7ae84925e62ed'),
    ObjectId('697e0687bbf11601d1fe9886'),
    ObjectId('697e0687bbf11601d1fe9887')
]

print("Checking Task IDs for Jan 19 Diaries:")
for tid in target_ids:
    d = db.diaries.find_one({'_id': tid})
    if d:
        print(f"ID: {tid} | TaskID: {d.get('task_id')} | ThreadStatus: {d.get('thread_status')}")
