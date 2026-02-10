from django.db import models
from django.conf import settings

from django.utils import timezone

class HaruOn(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='diaries')
    content = models.TextField(verbose_name="일기 내용")
    mood_score = models.IntegerField(verbose_name="감정 점수 (1-10)")
    analysis_result = models.JSONField(verbose_name="AI 분석 결과", null=True, blank=True)
    is_high_risk = models.BooleanField(default=False, verbose_name="위험 징후")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="작성일")

    class Meta:
        verbose_name = "하루온 (감정 일기)"
        verbose_name_plural = "하루온 목록"
        ordering = ['-created_at']
        db_table = "maum_on_maumon" # [Safe Migration] Keep existing table name to avoid data loss during rename

    def __str__(self):
        return f"{self.user.username}의 일기 ({self.created_at.strftime('%Y-%m-%d')})"
