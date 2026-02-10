from rest_framework import views, status, permissions
from rest_framework.response import Response
from pymongo import MongoClient
from datetime import datetime, timedelta
import os

# MongoDB Connection (vibe_coding 217 Server)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/mood_diary")
client = MongoClient(MONGO_URI)
db = client.mood_diary # Database: mood_diary (Default)

class PatientListView(views.APIView):
    """
    [Migration] Native MongoDB Implementation for InsightMind
    Replaces Django SQL ORM with PyMongo Direct Access
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            # 1. Fetch Users from MongoDB (member collection)
            # Find users who have nickname (active users)
            users = list(db.member.find({}, {'email': 1, 'nickname': 1, 'created_at': 1}))
            
            data = []
            for u in users:
                user_id = str(u.get('_id'))
                email = u.get('email', 'unknown')
                nickname = u.get('nickname', 'No Name')
                joined_at = u.get('created_at', datetime.now())

                # 2. Count Diaries (diary collection)
                # Ensure user_id is string in diary (vibe_coding standard: string)
                d_count = db.diary.count_documents({'user_id': user_id})
                
                # 3. Risk Count (mood_score <= 2)
                r_count = db.diary.count_documents({'user_id': user_id, 'mood_score': {'$lte': 2}})
                
                data.append({
                    'id': user_id,
                    'username': email,
                    'name': nickname,
                    'email': email,
                    'diary_count': d_count,
                    'risk_count': r_count,
                    'is_active': True,
                    'joined_at': joined_at
                })
                
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class PatientDetailView(views.APIView):
    """
    [Migration] Detailed Patient View (MongoDB)
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, user_id):
        from bson.objectid import ObjectId
        try:
            # Try ObjectId first
            try:
                oid = ObjectId(user_id)
                user = db.member.find_one({'_id': oid})
            except:
                # Fallback: String ID or Email? (Usually _id is OID)
                user = db.member.find_one({'_id': user_id})
                
            if not user:
                return Response({'error': 'User not found'}, status=404)
            
            # Fetch Diaries (Sort by created_at DESC)
            diaries_cursor = db.diary.find({'user_id': str(user.get('_id'))}).sort('created_at', -1)
            
            diaries_data = []
            for d in diaries_cursor:
                mood_score = d.get('mood_score', 3)
                diaries_data.append({
                    'id': str(d.get('_id')),
                    'created_at': d.get('created_at'),
                    'mood_score': mood_score,
                    'content': d.get('content', ''),
                    'keywords': d.get('keywords', []), # Extra field
                    'is_high_risk': mood_score <= 2
                })
                
            return Response({
                'patient': {
                    'id': str(user.get('_id')),
                    'username': user.get('email'),
                    'name': user.get('nickname', ''),
                    'email': user.get('email'),
                    'joined_at': user.get('created_at')
                },
                'diaries': diaries_data
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def post(self, request, user_id):
        """
        [New] Analysis Logic (MongoDB Version)
        """
        try:
            # Fetch Recent Diaries (Limit 10)
            # Ensure user_id matches format in DB (String)
            recent_diaries = list(db.diary.find({'user_id': user_id}).sort('created_at', -1).limit(10))
            
            if not recent_diaries:
                return Response({'result': "분석할 데이터가 부족합니다."}, status=200)

            # Analysis Logic
            scores = [d.get('mood_score', 3) for d in recent_diaries]
            count = len(scores)
            avg_score = sum(scores) / count
            risk_cnt = sum(1 for s in scores if s <= 2)
            
            # Generate Text
            if avg_score >= 4.0:
                 insight = f"최근 {count}건 분석 결과 양호합니다. (평균 {avg_score:.1f}점)"
            elif avg_score >= 2.5:
                 insight = f"최근 {count}건 중 감정 기복이 관찰됩니다. (평균 {avg_score:.1f}점, 위험 {risk_cnt}회)"
            else:
                 insight = f"⚠️ [위험] 최근 {count}건 중 {risk_cnt}회가 위험 수준입니다. (평균 {avg_score:.1f}점)"

            return Response({'result': insight})
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)
