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
        return redirect('/articles/')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            if user.role == 'editor':
                return redirect('editor-review')
            elif user.role == 'publisher':
                # FIXED: Use owned_publications (matches related_name in models.py)
                pub = user.owned_publications.first()
                if pub:
                    return redirect('manage-publication', pk=pub.pk)
                return redirect('/articles/')
            else:
                return redirect('/articles/')
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
            return redirect('/articles/')
    else:
        form = CustomUserCreationForm()
    return render(request, 'news/register.html', {'form': form})


def publisher_register(request):
    """View for users to register specifically as a Publisher."""
    if request.user.is_authenticated:
        return redirect('/articles/')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = CustomUser.ROLE_PUBLISHER
            user.save()

            # FIXED: Use owned_publications (matches related_name in models.py)
            if not user.owned_publications.exists():
                publication_name = f"{user.username}'s Publication"
                publication = Publisher.objects.create(
                    owner=user,
                    name=publication_name,
                    description=f"Publication owned by {user.username}"
                )
                messages.success(
                    request, 
                    f'Welcome, {user.username}! Your publication "{publication.name}" has been created.'
                )
            else:
                publication = user.owned_publications.first()
                messages.info(
                    request, 
                    f'Welcome back, {user.username}! Your publication "{publication.name}" is ready.'
                )

            login(request, user)
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
        return redirect('/articles/')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        publisher_id = request.POST.get('publisher')

        if title and content:
            # FIX #3: Auto-approve if no publisher is selected (Independent Article)
            is_independent = (not publisher_id or publisher_id == '')
            
            article = Article.objects.create(
                title=title,
                content=content,
                author=request.user,
                approved=is_independent # True if independent, False if linked to publisher
            )
            
            # Only link publisher if one was actually selected
            if not is_independent:
                try:
                    pub = Publisher.objects.get(id=publisher_id)
                    article.publisher = pub
                    article.save()
                except Publisher.DoesNotExist:
                    pass
            
            messages.success(request, 'Article submitted successfully!')
            return redirect('/articles/')
        else:
            messages.error(request, 'Title and Content are required.')

    publishers = Publisher.objects.all()
    return render(request, 'news/create_article.html', {'publishers': publishers})


@login_required
def edit_article(request, pk):
    """Allow journalists to edit their own articles."""
    article = get_object_or_404(Article, pk=pk)
    
    if article.author != request.user:
        messages.error(request, 'You can only edit your own articles.')
        return redirect('/articles/')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if title and content:
            article.title = title
            article.content = content
            article.approved = False
            article.save()
            messages.success(request, 'Article updated successfully!')
            return redirect('/articles/')
        else:
            messages.error(request, 'Title and Content are required.')

    return render(request, 'news/edit_article.html', {'article': article})


@login_required
def delete_article(request, pk):
    """Allow journalists to delete their own articles."""
    article = get_object_or_404(Article, pk=pk)
    
    if article.author != request.user:
        messages.error(request, 'You can only delete your own articles.')
        return redirect('/articles/')

    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article deleted successfully.')
        return redirect('/articles/')

    return render(request, 'news/confirm_delete_article.html', {'article': article})


@login_required
def article_detail_web(request, pk):
    """Display a single article detail page."""
    article = get_object_or_404(Article, pk=pk)
    if request.user.role == 'reader' and not article.approved:
        messages.error(request, 'This article has not been approved yet.')
        return redirect('/articles/')
    return render(request, 'news/article_detail.html', {'article': article})


@login_required
def editor_review(request):
    """Editor-only view showing all PENDING articles for review."""
    if not is_editor(request.user):
        return redirect('/articles/')
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


@login_required
def my_feed(request):
    """Show articles from subscribed publishers and journalists."""
    if request.user.role != 'reader':
        messages.error(request, "Only readers can access My Feed.")
        return redirect('/articles/')
    
    # Get articles from subscribed publishers
    pub_articles = Article.objects.filter(
        approved=True,
        publisher__in=request.user.subscribed_publishers.all()
    )
    
    # Get articles from subscribed journalists (independent articles)
    journalist_articles = Article.objects.filter(
        approved=True,
        author__in=request.user.subscribed_journalists.all(),
        publisher__isnull=True # Only independent articles
    )
    
    # Combine and order by date
    from django.db.models import Q
    articles = Article.objects.filter(
        Q(id__in=pub_articles.values('id')) | 
        Q(id__in=journalist_articles.values('id'))
    ).distinct().order_by('-created_at')
    
    return render(request, 'news/my_feed.html', {'articles': articles})


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
        return redirect('/newsletters/')

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
            return redirect('/newsletters/')
        else:
            messages.error(request, 'Title is required.')

    available_articles = Article.objects.filter(approved=True).order_by('-created_at')
    return render(request, 'news/create_newsletter.html', {'articles': available_articles})


@login_required
def manage_subscriptions(request):
    """Allow readers to manage their subscriptions."""
    if request.user.role != 'reader':
        messages.error(request, 'Only readers can manage subscriptions.')
        return redirect('/articles/')

    publishers = Publisher.objects.all().order_by('name')
    journalists = CustomUser.objects.filter(role='journalist').order_by('username')

    subscribed_publishers = set(request.user.subscribed_publishers.values_list('id', flat=True))
    subscribed_journalists = set(request.user.subscribed_journalists.values_list('id', flat=True))

    context = {
        'publishers': publishers,
        'journalists': journalists,
        'subscribed_publishers': subscribed_publishers,
        'subscribed_journalists': subscribed_journalists,
    }
    return render(request, 'news/manage_subscriptions.html', context)


@login_required
def toggle_subscription(request, content_type, object_id):
    """Handle subscribing/unsubscribing via POST request."""
    if request.user.role != 'reader' or request.method != 'POST':
        return HttpResponseForbidden('Method not allowed.')

    if content_type == 'publisher':
        pub = get_object_or_404(Publisher, pk=object_id)
        if pub in request.user.subscribed_publishers.all():
            request.user.subscribed_publishers.remove(pub)
            messages.success(request, f'Unsubscribed from "{pub.name}".')
        else:
            request.user.subscribed_publishers.add(pub)
            messages.success(request, f'Subscribed to "{pub.name}"!')
            
    elif content_type == 'journalist':
        journalist = get_object_or_404(CustomUser, pk=object_id, role='journalist')
        if journalist in request.user.subscribed_journalists.all():
            request.user.subscribed_journalists.remove(journalist)
            messages.success(request, f'Unsubscribed from {journalist.username}.')
        else:
            request.user.subscribed_journalists.add(journalist)
            messages.success(request, f'Subscribed to {journalist.username}!')
    else:
        messages.error(request, 'Invalid subscription type.')

    return redirect('manage-subscriptions')


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


@login_required
def setup_publication(request):
    """Allow publishers to create their first publication."""
    if request.user.role != 'publisher':
        messages.error(request, "Only publishers can set up publications.")
        return redirect('/articles/')
    
    existing_pub = Publisher.objects.filter(owner=request.user).first()
    if existing_pub:
        return redirect('manage-publication', pk=existing_pub.pk)
        
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            Publisher.objects.create(
                name=name, 
                owner=request.user,
                description=description
            )
            messages.success(request, f"'{name}' has been created successfully!")
            return redirect('/articles/')
        else:
            messages.error(request, "Publication name is required.")
            
    return render(request, 'news/setup_publication.html')


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
    
    
@login_required
def publish_independent_article(request, pk):
    """Allow journalists to publish their own pending independent articles."""
    if request.method != 'POST':
        return HttpResponseForbidden()
    
    # Get the article, ensuring it belongs to the current user
    article = get_object_or_404(Article, pk=pk, author=request.user)
    
    # Safety check: Only allow publishing if it has NO publisher
    if article.publisher:
        messages.error(request, "Articles linked to a publisher must be approved by an editor.")
    elif article.approved:
        messages.info(request, "This article is already published.")
    else:
        # Approve the article instantly
        article.approved = True
        article.save()
        messages.success(request, "Article published successfully!")
        
    return redirect('/articles/')