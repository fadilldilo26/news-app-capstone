from . import views
from django.urls import path, include

# Web Views Only
from .views import (
    custom_login, custom_logout, register, publisher_register,
    article_list_web, create_article, edit_article, delete_article,
    article_detail_web, editor_review, approve_article_web,
    newsletter_list_web, create_newsletter, manage_publication,
    manage_subscriptions, setup_publication, toggle_subscription,
)

urlpatterns = [
    # --- ROOT URL (MUST BE FIRST) ---
    # This ensures http://127.0.0.1:8000/ loads your login page, not the API
    path('', custom_login, name='custom-login'),

    # --- Authentication & Registration ---
    path('register/', register, name='register'),
    path('accounts/publisher-register/', publisher_register, name='publisher-register'),
    path('accounts/logout/', custom_logout, name='logout'),

    # --- Article Management ---
    path('articles/', article_list_web, name='article-list'),
    path('articles/create/', create_article, name='create-article'),
    path('articles/<int:pk>/edit/', edit_article, name='edit-article'),
    path('articles/<int:pk>/delete/', delete_article, name='delete-article'),
    path('articles/<int:pk>/', article_detail_web, name='article-detail-web'),
    path('articles/<int:pk>/approve/', approve_article_web, name='approve-article-web'),
    path('feed/', views.my_feed, name='my-feed'),
    path('articles/<int:pk>/publish/', views.publish_independent_article, name='publish-independent'),
    
    # --- Editor Workflow ---
    path('editor/review/', editor_review, name='editor-review'),

    # --- Newsletter Management ---
    path('newsletters/', newsletter_list_web, name='newsletter-list'),
    path('newsletters/create/', create_newsletter, name='create-newsletter'),

    # --- Publisher Management ---
    path('publications/<int:pk>/manage/', manage_publication, name='manage-publication'),
    path('publications/setup/', setup_publication, name='setup-publication'),
    
    # --- Reader Subscriptions ---
    path('subscriptions/', manage_subscriptions, name='manage-subscriptions'),
    path('subscriptions/toggle/<str:content_type>/<int:object_id>/', toggle_subscription, name='toggle-subscription'),

    # --- API Endpoints (Modular Include) ---
    # Note: This is mounted at 'api/', so it won't conflict with the root ''
    path('api/', include('news.api_urls')),
]