from rest_framework.authtoken.views import obtain_auth_token
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# DRF API ViewSets
from news.views import (
    ArticleViewSet, NewsletterViewSet, 
    PublisherViewSet, UserViewSet,
    approved_articles_log,
)

# Web Views
from news.views import (
    custom_login, custom_logout, register, publisher_register,
    article_list_web, create_article, article_detail_web,
    editor_review, approve_article_web,
    newsletter_list_web, create_newsletter, manage_publication,
)

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'newsletters', NewsletterViewSet, basename='newsletter')
router.register(r'publishers', PublisherViewSet, basename='publisher')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- API Endpoints ---
    path('api/', include(router.urls)),
    path('api/approved/', approved_articles_log, name='approved-articles-log'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/token/', obtain_auth_token, name='api-token'),

    # --- Web UI Endpoints ---
    path('', custom_login, name='custom-login'),
    path('register/', register, name='register'),
    path('accounts/publisher-register/', publisher_register, name='publisher-register'),
    path('accounts/logout/', custom_logout, name='logout'),
    
    path('articles/', article_list_web, name='article-list'),
    path('articles/create/', create_article, name='create-article'),
    path('articles/<int:pk>/', article_detail_web, name='article-detail'),
    path('articles/<int:pk>/approve/', approve_article_web, name='article-approve'),
    
    path('editor/review/', editor_review, name='editor-review'),
    
    path('newsletters/', newsletter_list_web, name='newsletter-list'),
    path('newsletters/create/', create_newsletter, name='create-newsletter'),
    
    path('publications/<int:pk>/manage/', manage_publication, name='manage-publication'),
]