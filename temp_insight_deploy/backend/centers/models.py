from django.db import models
from django.utils.crypto import get_random_string

class Center(models.Model):
    name = models.CharField(max_length=100, verbose_name="센터명")
    region = models.CharField(max_length=50, verbose_name="관할 지역")
    admin_email = models.EmailField(verbose_name="담당자 이메일")
    # [Fix] B2G Verification Code (Mapped to PG 'code' column)
    code = models.CharField(max_length=50, null=True, blank=True, verbose_name="기관 식별 코드")

    class Meta:
        verbose_name = "보건소/센터"
        verbose_name_plural = "보건소/센터 목록"

    def __str__(self):
        return self.name

class VerificationCode(models.Model):
    code = models.CharField(max_length=12, unique=True, verbose_name="인증 코드")
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='verification_codes')
    is_used = models.BooleanField(default=False, verbose_name="사용 여부")
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='used_codes')

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = get_random_string(length=10).upper()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "일회용 인증 코드"
        verbose_name_plural = "일회용 인증 코드 목록"
