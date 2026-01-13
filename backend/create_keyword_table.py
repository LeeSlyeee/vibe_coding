from sqlalchemy import create_engine, text

DATABASE_URI = 'mysql+pymysql://root:1q2w3e4r@127.0.0.1:3306/mood_diary'

def add_keyword_table():
    engine = create_engine(DATABASE_URI)
    with engine.connect() as conn:
        try:
            # Create EmotionKeyword table
            sql = text("""
            CREATE TABLE IF NOT EXISTS emotion_keywords (
                id INT AUTO_INCREMENT PRIMARY KEY,
                keyword VARCHAR(100) NOT NULL UNIQUE,
                emotion_label INT NOT NULL,
                frequency INT DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.execute(sql)
            print("Successfully created emotion_keywords table.")
        except Exception as e:
            print(f"Error creating table: {e}")

if __name__ == "__main__":
    add_keyword_table()
