"""
Memory Manager - Native RAG 구현 (Direct RAG)
Mem0 등의 복잡한 라이브러리에 의존하지 않고,
HuggingFace (sentence-transformers)와 PostgreSQL (pgvector)를
직접 사용하여 가볍고 안정적인 기억 저장 및 검색을 수행합니다.
"""

import os
import json
import logging
import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
from crypto_utils import EncryptionManager
import threading

load_dotenv()
crypto = EncryptionManager(os.environ.get('ENCRYPTION_KEY'))

logger = logging.getLogger(__name__)

# DB 접속 설정 (기본값)
DB_USER = os.environ.get("DB_USER", "vibe_user")
DB_PASS = os.environ.get("DB_PASS", "")  # [Fix] Gemini 버그 헌팅: 비밀번호 하드코딩 완전 제거
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "vibe_db")

# 임베딩 모델 싱글톤 초기화
_embedder = None
_embedder_lock = threading.Lock()

def get_embedder():
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    _embedder = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
                    logger.info("[MemoryManager] Native Embedder 초기화 완료")
                except Exception as e:
                    logger.error(f"[MemoryManager] Embedder 초기화 실패: {e}")
    return _embedder

def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        conn = psycopg2.connect(db_url)
    else:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    
    # pgvector 타입 등록 (벡터 삽입/검색용)
    register_vector(conn)
    return conn

def store_diary_memory(diary_id: int, user_id: int, diary_text: str, mood_level: int,
                       emotion_desc: str = "", ai_comment: str = "",
                       diary_date: str = ""):
    """
    일기 작성 시 핵심 내용을 PostgreSQL(pgvector)에 바로 저장합니다. (UPSERT 수행)
    """
    try:
        # 기억에 저장할 텍스트 구성
        memory_parts = []
        if diary_date:
            memory_parts.append(f"[{diary_date}]")
        memory_parts.append(f"기분점수: {mood_level}/5")
        if emotion_desc:
            memory_parts.append(f"감정: {emotion_desc}")
        if diary_text:
            truncated = diary_text[:200] if len(diary_text) > 200 else diary_text
            memory_parts.append(f"일기내용: {truncated}")
            
        if ai_comment:
            comment_text = ai_comment
            try:
                json_start = ai_comment.find('{')
                if json_start >= 0:
                    parsed = json.loads(ai_comment[json_start:])
                    if isinstance(parsed, dict):
                        comment_text = parsed.get('comment', '') or ai_comment
            except Exception:
                pass
            if comment_text:
                memory_parts.append(f"AI의견: {comment_text[:150]}")
                
        memory_text = " | ".join(memory_parts)
        
        embedder = get_embedder()
        if not embedder:
            logger.warning("[MemoryManager] Embedder 미초기화. 메모리 저장 생략.")
            return
            
        # 벡터 인코딩 (평문 기준으로 벡터 생성)
        embedding = embedder.encode(memory_text).tolist()
        
        # DB 저장용 텍스트 암호화
        encrypted_text = crypto.encrypt(memory_text)
        
        # DB에 바로 삽입
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            query = """
                INSERT INTO diary_memories (diary_id, user_id, memory_text, embedding)
                VALUES (%s, %s, %s, %s::vector)
                ON CONFLICT (diary_id) DO UPDATE 
                SET memory_text = EXCLUDED.memory_text,
                    embedding = EXCLUDED.embedding
            """
            cur.execute(query, (diary_id, user_id, encrypted_text, embedding))
            conn.commit()
            cur.close()
            logger.info(f"[MemoryManager] 유저 {user_id} 기억 직접 저장 완료 (Native RAG)")
        finally:
            conn.close()
        
    except Exception as e:
        logger.error(f"[MemoryManager] 메모리 직접 저장 실패 (유저 {user_id}): {e}")


def recall_memories(user_id: int, current_text: str, limit: int = 5, exclude_diary_id: int = None) -> str:
    """
    현재 일기 내용과 일치(유사)하는 과거 기억을 벡터 검색으로 불러옵니다.
    본인 일기 수정 시 자기 참조 환각을 막기 위해 exclude_diary_id를 제공받습니다.
    """
    try:
        if not current_text or not current_text.strip():
            logger.info("[MemoryManager] 검색 대상 문자열이 비어있어, 장기 기억 검색을 생략합니다.")
            return ""
            
        embedder = get_embedder()
        if not embedder:
            logger.warning("[MemoryManager] Embedder 미초기화. 메모리 검색 생략.")
            return ""
            
        # 검색 쿼리를 벡터로 변환
        search_vector = embedder.encode(current_text).tolist()
        
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            
            if exclude_diary_id is not None:
                query = """
                    SELECT memory_text 
                    FROM diary_memories 
                    WHERE user_id = %s AND diary_id != %s
                    ORDER BY embedding <=> %s::vector 
                    LIMIT %s
                """
                cur.execute(query, (user_id, exclude_diary_id, search_vector, limit))
            else:
                query = """
                    SELECT memory_text 
                    FROM diary_memories 
                    WHERE user_id = %s 
                    ORDER BY embedding <=> %s::vector 
                    LIMIT %s
                """
                cur.execute(query, (user_id, search_vector, limit))
                
            rows = cur.fetchall()
            cur.close()
        finally:
            conn.close()
        
        if not rows:
            return ""
            
        memories = []
        for row in rows:
            try:
                dec = crypto.decrypt(row[0])
                memories.append(f"  - {dec}")
            except Exception as dec_err:
                logger.error(f"[MemoryManager] 복호화 에러: {dec_err}")
                continue
                
        context = "【사용자의 과거 기록 요약】\n" + "\n".join(memories)
        
        logger.info(f"[MemoryManager] 유저 {user_id} 기억 {len(memories)}건 회상 완료 (Native RAG)")
        return context
        
    except Exception as e:
        logger.error(f"[MemoryManager] 메모리 검색 실패 (유저 {user_id}): {e}")
        return ""


def get_user_memory_count(user_id: int) -> int:
    """특정 사용자의 저장된 기억 개수를 반환합니다."""
    try:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM diary_memories WHERE user_id = %s", (user_id,))
            count = cur.fetchone()[0]
            cur.close()
            return count
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"[MemoryManager] 메모리 카운트 실패 (유저 {user_id}): {e}")
        return 0

def delete_diary_memory(diary_id: int):
    """
    일기가 완전히 삭제될 때 RAG 메모리(diary_memories)에서도 해당 일기의 벡터를 지워
    고아 데이터(Zombie Data)로 남는 보안 사고를 방지합니다.
    """
    try:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM diary_memories WHERE diary_id = %s", (diary_id,))
            conn.commit()
            cur.close()
            logger.info(f"[MemoryManager] 일기 {diary_id} 의 RAG 메모리 파기 완료 (Zero-Trace)")
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"[MemoryManager] 일기 {diary_id} 메모리 파기 실패: {e}")

