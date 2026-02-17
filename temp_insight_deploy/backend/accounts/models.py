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
        managed = True
        db_table = 'users_user'
        verbose_name = "사용자"
        verbose_name_plural = "사용자 목록"

class LegacyUser(models.Model):
    """
    Maps to the existing 'users' table in vibe_db (Patient Data).
    """
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=80, unique=True, verbose_name="아이디")
    real_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="실명")
    password = models.CharField(max_length=200, verbose_name="비밀번호(Hash)")
    center_code = models.CharField(max_length=50, null=True, blank=True, verbose_name="센터 코드")
    role = models.CharField(max_length=20, null=True, blank=True, verbose_name="역할")
    created_at = models.DateTimeField(null=True, blank=True, verbose_name="가입일")

    class Meta:
        managed = False
        db_table = 'users'
        verbose_name = "환자 (Legacy)"
        verbose_name_plural = "환자 목록 (Legacy)"

    def __str__(self):
        return self.username

