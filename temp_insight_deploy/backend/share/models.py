from django.db import models
from django.conf import settings
import random
import string
from django.utils import timezone

def generate_share_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class ShareCode(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='share_code')
    code = models.CharField(max_length=10, unique=True, default=generate_share_code)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.code}"

class ShareConnection(models.Model):
    # sharer: 내 정보를 공유하는 사람 (환자)
    # viewer: 정보를 보는 사람 (보호자)
    sharer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sharer_connections')
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='viewer_connections')
    connected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('sharer', 'viewer')
    
    def __str__(self):
        return f"{self.sharer} -> {self.viewer}"
