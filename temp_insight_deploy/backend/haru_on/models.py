from django.db import models
from django.conf import settings
from django.utils import timezone

class HaruOn(models.Model):
    # [Hard Transition] PostgreSQL Table Mapping
    # Match Flask 'diaries' table schema
    
    # user_id (ForeignKey)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='diaries', db_column='user_id')
    
    # Core Content
    content = models.TextField(verbose_name="일기 내용", db_column='event', null=True)
    mood_score = models.IntegerField(verbose_name="감정 점수 (1-10)", db_column='mood_intensity', default=3)
    
    # Additional Fields (Unmanaged in Django, mapped to PG columns)
    emotion_desc = models.TextField(null=True)
    emotion_meaning = models.TextField(null=True)
    self_talk = models.TextField(null=True)
    ai_comment = models.TextField(null=True)
    ai_emotion = models.TextField(null=True)
    
    is_high_risk = models.BooleanField(default=False, verbose_name="위험 징후", db_column='safety_flag') # Map to 'safety_flag' if exists, or maintain separate field? 
    # Flask has 'safety_flag'. Django uses 'is_high_risk'.
    # Update Django to map 'is_high_risk' -> 'safety_flag' column.
    
    # analysis_result removed as PG schema uses columns
    # analysis_result = models.JSONField(...) 
    # If PG has JSON column named 'analysis_result', use it. 
    # If Flask schema has separate columns, Django JSONField won't work unless column exists.
    # Flask schema doesn't seem to have 'analysis_result' JSON column! It has separate columns.
    # So we remove 'analysis_result' or make it a dummy property?
    # Better: Keep it as unmanaged if needed, but for now let's map real columns.
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name="작성일")

    class Meta:
        managed = False # Do not create table via Django
        db_table = "diaries" # Match Flask Table Name
        verbose_name = "하루온 (감정 일기)"
        verbose_name_plural = "하루온 목록"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}의 일기 ({self.created_at.strftime('%Y-%m-%d')})"
