# news/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ArticleViewSet, NewsletterViewSet,
    PublisherViewSet, UserViewSet,
    approved_articles_log,
)

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'newsletters', NewsletterViewSet, basename='newsletter')
router.register(r'publishers', PublisherViewSet, basename='publisher')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('approved/', approved_articles_log, name='approved-articles-log'),
]