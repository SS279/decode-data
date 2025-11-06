from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, LearnerProgress, ModelEdit, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model"""
    list_display = ('username', 'email', 'schema_name', 'is_staff', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'schema_name')
    readonly_fields = ('created_at', 'last_login', 'date_joined')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Learner Information', {'fields': ('schema_name', 'created_at')}),
    )


@admin.register(LearnerProgress)
class LearnerProgressAdmin(admin.ModelAdmin):
    """Admin interface for LearnerProgress model"""
    list_display = ('user', 'lesson_id', 'lesson_progress', 'queries_run', 'last_updated')
    list_filter = ('lesson_id', 'lesson_progress', 'last_updated')
    search_fields = ('user__username', 'lesson_id')
    readonly_fields = ('last_updated',)
    
    fieldsets = (
        ('Learner', {'fields': ('user', 'lesson_id')}),
        ('Progress', {'fields': ('lesson_progress', 'completed_steps', 'models_executed', 'queries_run')}),
        ('Quiz', {'fields': ('quiz_answers', 'quiz_score')}),
        ('Metadata', {'fields': ('last_updated',)}),
    )


@admin.register(ModelEdit)
class ModelEditAdmin(admin.ModelAdmin):
    """Admin interface for ModelEdit model"""
    list_display = ('user', 'lesson_id', 'model_name', 'last_updated')
    list_filter = ('lesson_id', 'last_updated')
    search_fields = ('user__username', 'lesson_id', 'model_name')
    readonly_fields = ('last_updated',)
    
    fieldsets = (
        ('Model Information', {'fields': ('user', 'lesson_id', 'model_name')}),
        ('SQL Content', {'fields': ('model_sql',)}),
        ('Metadata', {'fields': ('last_updated',)}),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin interface for UserSession model"""
    list_display = ('user', 'session_key', 'is_active', 'created_at', 'last_activity')
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__username', 'session_key')
    readonly_fields = ('created_at', 'last_activity')
    
    fieldsets = (
        ('Session', {'fields': ('user', 'session_key', 'is_active')}),
        ('Workspace', {'fields': ('dbt_workspace_path',)}),
        ('Timestamps', {'fields': ('created_at', 'last_activity')}),
    )