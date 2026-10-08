from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Publisher, Article, Newsletter


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom admin for the CustomUser model."""
    
    # Add 'role' to the fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Subscriptions', {
            'fields': ('role', 'subscribed_publishers', 'subscribed_journalists'),
        }),
    )
    
    # Add 'role' to the add form
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role', {
            'fields': ('role',),
        }),
    )
    
    list_display = ['username', 'email', 'role', 'is_staff']
    list_filter = ['role', 'is_staff']
    search_fields = ['username', 'email']


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Admin for Publisher model."""
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin for Article model."""
    list_display = ['title', 'author', 'publisher', 'approved', 'created_at']
    list_filter = ['approved', 'author', 'publisher']
    search_fields = ['title', 'content']
    actions = ['approve_articles']

    def approve_articles(self, request, queryset):
        """Bulk approve selected articles."""
        updated = queryset.update(approved=True)
        self.message_user(request, f'{updated} articles approved.')
    approve_articles.short_description = 'Approve selected articles'


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Admin for Newsletter model."""
    list_display = ['title', 'author', 'created_at']
    list_filter = ['author']
    search_fields = ['title', 'description']