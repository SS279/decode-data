"""URL Configuration for learning app"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('blogs/', views.blogs_view, name='blogs'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Lessons
    path('lesson/<str:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<str:lesson_id>/builder/', views.model_builder, name='model_builder'),
    path('lesson/<str:lesson_id>/query/', views.query_visualize, name='query_visualize'),
    path('lesson/<str:lesson_id>/progress/', views.progress_dashboard, name='progress_dashboard'),
    
    # API Endpoints
    path('api/get-model-content/', views.api_get_model_content, name='api_get_model_content'),
    path('api/validate-lesson/', views.api_validate_lesson, name='api_validate_lesson'),

    # AI Assistant
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
    path('api/ai/chat/', views.ai_chat, name='ai_chat'),
    path('api/ai/analyze/', views.analyze_model, name='analyze_model'),
    path('api/ai/generate-tests/', views.generate_test, name='generate_test')
]