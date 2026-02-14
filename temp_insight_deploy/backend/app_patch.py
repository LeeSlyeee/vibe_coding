
# Smart Lookup Logic for Flask
    user_id = get_jwt_identity()
    user = None
    
    # [Smart Lookup] Support both Django ID (int) and Flask ID (ObjectId)
    if isinstance(user_id, int):
        user = mongo.db.users.find_one({'django_id': user_id})
        if not user:
             # Fallback: Try to find by username if possible? No, we don't have username in token.
             # But wait, maybe we can query by 'id' field if migrated?
             user = mongo.db.users.find_one({'id': user_id}) 
    else:
        try:
            user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        except:
            pass

    if not user:
        return jsonify({'message': 'User not found'}), 404
