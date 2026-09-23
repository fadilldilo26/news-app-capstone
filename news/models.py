from django.contrib.auth.models import AbstractUser, Group
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Adds a role field and subscription relationships for Readers,
    and reverse relations for Journalists.
    """
    ROLE_READER = 'reader'
    ROLE_EDITOR = 'editor'
    ROLE_JOURNALIST = 'journalist'
    ROLE_PUBLISHER = 'publisher' # NEW ROLE ADDED

    ROLE_CHOICES = [
        (ROLE_READER, 'Reader'),
        (ROLE_EDITOR, 'Editor'),
        (ROLE_JOURNALIST, 'Journalist'),
        (ROLE_PUBLISHER, 'Publisher'), # NEW CHOICE ADDED
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_READER,
        help_text="The role assigned to this user."
    )

    # --- Fields for READER role ---
    subscribed_publishers = models.ManyToManyField(
        'Publisher',
        related_name='subscribers',
        blank=True,
        help_text="Publishers this reader is subscribed to."
    )

    subscribed_journalists = models.ManyToManyField(
        'self',
        related_name='subscriber_readers',
        symmetrical=False,
        blank=True,
        limit_choices_to={'role': 'journalist'},
        help_text="Journalists this reader is subscribed to."
    )

    def save(self, *args, **kwargs):
        """
        Override save to:
        1. Automatically assign user to correct Django Group based on role.
        2. Clear irrelevant subscription fields based on role.
        """
        # Save first to ensure the user has a PK
        super().save(*args, **kwargs)

        # Get or create groups for each role
        reader_group, _ = Group.objects.get_or_create(name='Readers')
        editor_group, _ = Group.objects.get_or_create(name='Editors')
        journalist_group, _ = Group.objects.get_or_create(name='Journalists')
        publisher_group, _ = Group.objects.get_or_create(name='Publishers') # NEW GROUP

        # Remove from all groups first
        self.groups.clear()

        # Add to the correct group and clear irrelevant fields
        if self.role == self.ROLE_READER:
            self.groups.add(reader_group)
        elif self.role == self.ROLE_EDITOR:
            self.groups.add(editor_group)
            # Clear reader subscription fields for editors
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()
        elif self.role == self.ROLE_JOURNALIST:
            self.groups.add(journalist_group)
            # Clear reader subscription fields for journalists
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()
        elif self.role == self.ROLE_PUBLISHER: # NEW LOGIC
            self.groups.add(publisher_group)
            # Clear reader subscription fields for publishers
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Publisher(models.Model):
    """Represents a news publisher/publication."""
    
    # UPDATED: Added null=True, blank=True to allow migration without default
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='owned_publications',
        limit_choices_to={'role': 'publisher'},
        null=True, # <--- ADDED THIS
        blank=True, # <--- ADDED THIS
        help_text="The publisher user who owns this publication"
    )

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # NEW: Fields to assign staff to this publication
    assigned_editors = models.ManyToManyField(
        CustomUser,
        related_name='assigned_to_publications_as_editor',
        limit_choices_to={'role': 'editor'},
        blank=True,
        help_text="Editors assigned to work on this publication"
    )

    assigned_journalists = models.ManyToManyField(
        CustomUser,
        related_name='assigned_to_publications_as_journalist',
        limit_choices_to={'role': 'journalist'},
        blank=True,
        help_text="Journalists assigned to work on this publication"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Publishers"


class Article(models.Model):
    """Represents a news article authored by a journalist."""
    title = models.CharField(max_length=300)
    content = models.TextField()
    
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='articles',
        help_text="The journalist who wrote this article."
    )
    
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        help_text="Publisher this article belongs to (optional)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    approved = models.BooleanField(
        default=False,
        help_text="Whether an editor has approved this article."
    )

    def __str__(self):
        status = "Approved" if self.approved else "Pending"
        return f"{self.title} ({status})"

    class Meta:
        ordering = ['-created_at']


class Newsletter(models.Model):
    """A curated collection of articles."""
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='newsletters',
        limit_choices_to={'role__in': ['journalist', 'editor']},
        help_text="Journalist or editor who created this newsletter."
    )
    
    articles = models.ManyToManyField(
        Article,
        related_name='newsletters',
        blank=True,
        help_text="Articles included in this newsletter."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']