from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.models import Group

from .models import Article, Newsletter, CustomUser, Publisher
from .forms import CustomUserCreationForm

# --- Helper: Check if user is Editor ---
def is_editor(user):
    """Return True if user has Editor role."""
    return user.is_authenticated and user.role == 'editor'

# ===========================
# AUTHENTICATION VIEWS
# ===========================

def custom_login(request):
    """Custom login view for the web interface."""
    if request.user.is_authenticated:
        return redirect('article-list')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect based on role
            if user.role == 'editor':
                return redirect('editor-review')
            elif user.role == 'publisher':
                pub = user.owned_publications.first()
                if pub:
                    return redirect('manage-publication', pk=pub.pk)
                return redirect('article-list')
            else:
                return redirect('article-list')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'news/login.html')

def custom_logout(request):
    """Logout view."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('custom-login')

def register(request):
    """Regular user registration (readers, journalists, editors)."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('article-list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'news/register.html', {'form': form})

def publisher_register(request):
    """View for users to register specifically as a Publisher."""
    if request.user.is_authenticated:
        return redirect('article-list')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = CustomUser.ROLE_PUBLISHER
            user.save() 

            publication_name = f"{user.username}'s Publication"
            publication = Publisher.objects.create(
                owner=user,
                name=publication_name,
                description=f"Publication owned by {user.username}"
            )

            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your publication "{publication.name}" has been created.')
            return redirect('manage-publication', pk=publication.pk)
    else:
        form = CustomUserCreationForm()

    return render(request, 'news/publisher_register.html', {'form': form})

# ===========================
# WEB VIEWS (Articles)
# ===========================

@login_required
def article_list_web(request):
    """Display list of articles based on user role."""
    user = request.user
    if user.role == 'journalist':
        articles = Article.objects.filter(author=user).order_by('-created_at')
    else:
        articles = Article.objects.filter(approved=True).order_by('-created_at')
    
    return render(request, 'news/article_list.html', {'articles': articles})

@login_required
def create_article(request):
    """Allow journalists to create a new article."""
    if request.user.role != 'journalist':
        messages.error(request, 'Only journalists can create articles.')
        return redirect('article-list')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        publisher_id = request.POST.get('publisher')
        
        if title and content:
            article = Article.objects.create(
                title=title,
                content=content,
                author=request.user,
                approved=False
            )
            
            if publisher_id:
                try:
                    pub = Publisher.objects.get(id=publisher_id)
                    article.publisher = pub
                    article.save()
                except Publisher.DoesNotExist:
                    pass

            messages.success(request, 'Article submitted for review!')
            return redirect('article-list')
        else:
            messages.error(request, 'Title and Content are required.')

    publishers = Publisher.objects.all()
    return render(request, 'news/create_article.html', {'publishers': publishers})

@login_required
def article_detail_web(request, pk):
    """Display a single article detail page."""
    article = get_object_or_404(Article, pk=pk)
    if request.user.role == 'reader' and not article.approved:
        messages.error(request, 'This article has not been approved yet.')
        return redirect('article-list')
    return render(request, 'news/article_detail.html', {'article': article})

@login_required
def editor_review(request):
    """Editor-only view showing all PENDING articles for review."""
    if not is_editor(request.user):
        return redirect('article-list')
    pending_articles = Article.objects.filter(approved=False).order_by('-created_at')
    return render(request, 'news/editor_review.html', {'pending_articles': pending_articles})

@login_required
def approve_article_web(request, pk):
    """Handle article approval via web form POST. Only editors."""
    if request.method != 'POST':
        return HttpResponseForbidden('Method not allowed.')
    article = get_object_or_404(Article, pk=pk)
    if article.approved:
        messages.warning(request, 'This article is already approved.')
    else:
        article.approved = True
        article.save()
        messages.success(request, f'Article "{article.title}" has been approved!')
    return redirect('editor-review')

# ===========================
# WEB VIEWS (Newsletters & Management)
# ===========================

@login_required
def newsletter_list_web(request):
    """Display list of newsletters (journalists and editors only)."""
    if request.user.role not in ['journalist', 'editor']:
        messages.error(request, 'You do not have permission.')
        return redirect('article-list')
    newsletters = Newsletter.objects.all().order_by('-created_at')
    return render(request, 'news/newsletter_list.html', {'newsletters': newsletters})

@login_required
def create_newsletter(request):
    """Allow journalists and editors to create a new newsletter."""
    if request.user.role not in ['journalist', 'editor']:
        messages.error(request, 'Only journalists and editors can create newsletters.')
        return redirect('newsletter-list')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        article_ids = request.POST.getlist('articles')
        
        if title:
            newsletter = Newsletter.objects.create(
                title=title,
                description=description,
                author=request.user
            )
            
            if article_ids:
                newsletter.articles.set(article_ids)
            
            messages.success(request, 'Newsletter created successfully!')
            return redirect('newsletter-list')
        else:
            messages.error(request, 'Title is required.')

    available_articles = Article.objects.filter(approved=True).order_by('-created_at')
    return render(request, 'news/create_newsletter.html', {'articles': available_articles})

@login_required
def manage_publication(request, pk):
    """Allows a Publisher to view and manage their publication."""
    publication = get_object_or_404(Publisher, pk=pk)
    if publication.owner != request.user:
        messages.error(request, 'You do not have permission to manage this publication.')
        return redirect('article-list')

    if request.method == 'POST':
        editor_ids = request.POST.getlist('editors')
        publication.assigned_editors.set(editor_ids)
        
        journalist_ids = request.POST.getlist('journalists')
        publication.assigned_journalists.set(journalist_ids)
        
        messages.success(request, 'Staff assignments updated successfully!')
        return redirect('manage-publication', pk=pk)

    available_editors = CustomUser.objects.filter(role='editor')
    available_journalists = CustomUser.objects.filter(role='journalist')
    
    context = {
        'publication': publication,
        'available_editors': available_editors,
        'available_journalists': available_journalists,
    }
    return render(request, 'news/manage_publication.html', context)


# ===========================
# DRF API VIEWSETS
# ===========================

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .serializers import ArticleSerializer, NewsletterSerializer, PublisherSerializer, UserSerializer
import logging

logger = logging.getLogger(__name__)

class ArticleViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if self.action == 'subscribed':
            if user.role == 'reader':
                return Article.objects.filter(
                    approved=True,
                    publisher__in=user.subscribed_publishers.all()
                ) | Article.objects.filter(
                    approved=True,
                    author__in=user.subscribed_journalists.all()
                )
        return Article.objects.filter(approved=True)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'])
    def subscribed(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        article = self.get_object()
        article.approved = True
        article.save()
        return Response({'status': 'Article approved', 'article_id': article.id})

class NewsletterViewSet(viewsets.ModelViewSet):
    serializer_class = NewsletterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Newsletter.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        article = self.get_object()
        return Response({'status': 'Article approved', 'article_id': article.id}, status=status.HTTP_200_OK)

class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def approved_articles_log(request):
    article_id = request.data.get('article_id')
    title = request.data.get('title')
    author = request.data.get('author')
    publisher = request.data.get('publisher')
    logger.info(f"Article approved: ID={article_id}, Title='{title}', Author={author}, Publisher={publisher}")
    return Response({
        'status': 'logged',
        'article_id': article_id,
        'message': f'Article "{title}" has been logged as approved.'
    }, status=status.HTTP_201_CREATED)