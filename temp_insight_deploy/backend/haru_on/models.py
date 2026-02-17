from django.db import models
from django.conf import settings
from django.utils import timezone

class HaruOn(models.Model):
    # [Hard Transition] PostgreSQL Table Mapping
    # Match Flask 'diaries' table schema
    
    # user_id (ForeignKey)
    # user_id (ForeignKey to Legacy 'users' table)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='diaries')
    
    # Core Content
    content = models.TextField(verbose_name="일기 내용", null=True)
    mood_score = models.IntegerField(verbose_name="감정 점수 (1-10)", default=3)
    
    # Additional Fields (Unmanaged in Django, mapped to PG columns)
    emotion_desc = models.TextField(null=True)
    emotion_meaning = models.TextField(null=True)
    self_talk = models.TextField(null=True)
    ai_comment = models.TextField(null=True)
    ai_emotion = models.TextField(null=True)
    
    # [New] Fields requested for full view
    sleep_condition = models.CharField(max_length=50, null=True, blank=True)
    weather = models.CharField(max_length=50, null=True, blank=True)
    temperature = models.CharField(max_length=50, null=True, blank=True)
    gratitude_note = models.TextField(null=True, blank=True)
    mode = models.CharField(max_length=50, null=True, blank=True) # e.g. 'voice' or 'text'
    
    is_high_risk = models.BooleanField(default=False, verbose_name="위험 징후")
    
    # ... (skipping removed analysis_result)
    
    analysis_result = models.JSONField(verbose_name="AI 분석 결과", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="작성일")

    class Meta:
        managed = True 
        db_table = "haru_on_diaries"
        verbose_name = "하루온 (감정 일기)"
        verbose_name_plural = "하루온 목록"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}의 일기 ({self.created_at.strftime('%Y-%m-%d')})"
