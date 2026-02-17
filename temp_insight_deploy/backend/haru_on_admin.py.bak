from django.contrib import admin

from .models import HaruOn

@admin.register(HaruOn)
class HaruOnAdmin(admin.ModelAdmin):
    list_display = ('user', 'mood_score', 'is_high_risk', 'created_at')
    list_filter = ('is_high_risk', 'created_at')
    search_fields = ('user__username', 'content')
