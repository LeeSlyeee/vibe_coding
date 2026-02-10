from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class RiskLevel(models.TextChoices):
        LOW = 'LOW', '관심 필요 없음'
        MID = 'MID', '주의 요망'
        HIGH = 'HIGH', '위험'

    risk_level = models.CharField(
        max_length=10,
        choices=RiskLevel.choices,
        default=RiskLevel.LOW,
        verbose_name="위험도 등급"
    )

    center = models.ForeignKey(
        'centers.Center',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name="소속 센터"
    )

    class Meta:
        verbose_name = "사용자"
        verbose_name_plural = "사용자 목록"
