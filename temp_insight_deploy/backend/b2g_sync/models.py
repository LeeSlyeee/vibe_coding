from django.db import models
from django.conf import settings

class B2GConnection(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', '승인 대기'
        ACTIVE = 'ACTIVE', '연동 중'
        REVOKED = 'REVOKED', '해지됨'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='connections')
    center = models.ForeignKey('centers.Center', on_delete=models.CASCADE, related_name='connections')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    consented_at = models.DateTimeField(auto_now_add=True, verbose_name="정보 제공 동의 일시")
    expired_at = models.DateTimeField(null=True, blank=True, verbose_name="만료 일시")

    class Meta:
        verbose_name = "기관 연동 정보"
        verbose_name_plural = "기관 연동 목록"

    def __str__(self):
        return f"{self.user.username} - {self.center.name} ({self.status})"
