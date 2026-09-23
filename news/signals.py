import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Article


@receiver(post_save, sender=Article)
def article_approved_signal(sender, instance, created, **kwargs):
    """
    Triggered when an Article is saved.
    If the article was just approved (approved=True), send email notifications
    and log to the /api/approved/ endpoint.
    """
    # Only trigger if the article is newly approved (not just created)
    if instance.approved and not created:
        # Check if this is a new approval (not already approved before)
        # We use a simple check: if approved is True now, send notifications
        
        # 1. Send email to subscribers
        send_approval_email(instance)
        
        # 2. Log to internal API endpoint
        log_to_approved_api(instance)


def send_approval_email(article):
    """
    Send email notification to subscribers of the article's publisher/journalist.
    """
    subject = f"New Approved Article: {article.title}"
    
    # Get the author (journalist) and publisher
    journalist = article.author
    publisher = article.publisher
    
    # Build the list of subscriber emails
    subscriber_emails = []
    
    # Add readers subscribed to this journalist
    if journalist:
        reader_emails = journalist.subscriber_readers.values_list(
            'email', flat=True
        )
        subscriber_emails.extend(reader_emails)
    
    # Add readers subscribed to this publisher
    if publisher:
        publisher_subscriber_emails = publisher.subscribers.values_list(
            'email', flat=True
        )
        subscriber_emails.extend(publisher_subscriber_emails)
    
    # Remove duplicates
    subscriber_emails = list(set(subscriber_emails))
    
    if subscriber_emails:
        message = (
            f"A new article has been approved and published!\n\n"
            f"Title: {article.title}\n"
            f"Author: {journalist.username if journalist else 'Unknown'}\n"
            f"Publisher: {publisher.name if publisher else 'Independent'}\n\n"
            f"Content Preview:\n{article.content[:200]}...\n\n"
            f"Visit our website to read the full article!"
        )
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@newsapp.com',
                recipient_list=subscriber_emails,
                fail_silently=False,
            )
            print(f"✅ Email sent to {len(subscriber_emails)} subscribers for article: {article.title}")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
    else:
        print(f"ℹ️ No subscribers found for article: {article.title}")


def log_to_approved_api(article):
    """
    Send a POST request to the internal /api/approved/ endpoint
    to log the approved article (simulates external sharing).
    """
    try:
        # Use localhost URL since this is internal
        api_url = "http://127.0.0.1:8000/api/approved/"
        
        payload = {
            'article_id': article.id,
            'title': article.title,
            'author': article.author.username,
            'publisher': article.publisher.name if article.publisher else None,
            'approved_at': str(article.updated_at),
        }
        
        response = requests.post(api_url, json=payload, timeout=5)
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"✅ Logged to /api/approved/: {article.title}")
        else:
            print(f"⚠️ API logging returned status {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️ Could not connect to /api/approved/ endpoint (server may not be running)")
    except Exception as e:
        print(f"❌ Failed to log to API: {e}")