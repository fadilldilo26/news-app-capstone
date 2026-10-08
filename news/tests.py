from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import Publisher, Article, Newsletter

CustomUser = get_user_model()


class ModelTests(TestCase):
    """Test the models."""

    def setUp(self):
        """Set up test data."""
        self.publisher = Publisher.objects.create(
            name='Tech Daily',
            description='Technology news'
        )
        
        self.journalist = CustomUser.objects.create_user(
            username='journalist1',
            password='testpass123',
            role='journalist'
        )
        
        self.editor = CustomUser.objects.create_user(
            username='editor1',
            password='testpass123',
            role='editor'
        )
        
        self.reader = CustomUser.objects.create_user(
            username='reader1',
            password='testpass123',
            role='reader'
        )
        self.reader.subscribed_publishers.add(self.publisher)
        self.reader.subscribed_journalists.add(self.journalist)
        
        self.article = Article.objects.create(
            title='Test Article',
            content='Test content',
            author=self.journalist,
            publisher=self.publisher,
            approved=False
        )

    def test_custom_user_role(self):
        """Test that user role is set correctly."""
        self.assertEqual(self.journalist.role, 'journalist')
        self.assertEqual(self.editor.role, 'editor')
        self.assertEqual(self.reader.role, 'reader')

    def test_article_creation(self):
        """Test article creation."""
        self.assertEqual(self.article.title, 'Test Article')
        self.assertFalse(self.article.approved)
        self.assertEqual(self.article.author, self.journalist)

    def test_publisher_creation(self):
        """Test publisher creation."""
        self.assertEqual(self.publisher.name, 'Tech Daily')

    def test_newsletter_creation(self):
        """Test newsletter creation."""
        newsletter = Newsletter.objects.create(
            title='Test Newsletter',
            description='Test description',
            author=self.journalist
        )
        newsletter.articles.add(self.article)
        self.assertEqual(newsletter.articles.count(), 1)


class ArticleApprovalSignalTest(APITestCase):
    """Test the article approval signal."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.publisher = Publisher.objects.create(
            name='Tech Daily',
            description='Technology news'
        )
        
        self.journalist = CustomUser.objects.create_user(
            username='journalist1',
            password='testpass123',
            role='journalist'
        )
        
        self.reader = CustomUser.objects.create_user(
            username='reader1',
            email='reader1@example.com',
            password='testpass123',
            role='reader'
        )
        self.reader.subscribed_publishers.add(self.publisher)
        
        self.article = Article.objects.create(
            title='Test Article',
            content='Test content',
            author=self.journalist,
            publisher=self.publisher,
            approved=False
        )

    @patch('news.signals.send_mail')
    @patch('news.signals.requests.post')
    def test_approval_triggers_email_and_api_log(self, mock_post, mock_send_mail):
        """Test that approving an article triggers email and API log."""
        # Mock the requests.post response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        # Approve the article
        self.article.approved = True
        self.article.save()
        
        # Verify email was sent
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        self.assertIn('reader1@example.com', call_args[1]['recipient_list'])
        
        # Verify API was called
        mock_post.assert_called_once()

    @patch('news.signals.send_mail')
    @patch('news.signals.requests.post')
    def test_no_email_when_no_subscribers(self, mock_post, mock_send_mail):
        """Test that no email is sent when there are no subscribers."""
        # Remove subscriber
        self.reader.subscribed_publishers.remove(self.publisher)
        
        # Mock the requests.post response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        # Approve the article
        self.article.approved = True
        self.article.save()
        
        # Verify email was NOT sent
        mock_send_mail.assert_not_called()


class APIPermissionTests(APITestCase):
    """Test API permissions per role."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.publisher = Publisher.objects.create(
            name='Tech Daily',
            description='Technology news'
        )
        
        # Create users with different roles
        self.journalist = CustomUser.objects.create_user(
            username='journalist1',
            password='testpass123',
            role='journalist'
        )
        
        self.editor = CustomUser.objects.create_user(
            username='editor1',
            password='testpass123',
            role='editor'
        )
        
        self.reader = CustomUser.objects.create_user(
            username='reader1',
            password='testpass123',
            role='reader'
        )
        
        # Create an approved article
        self.article = Article.objects.create(
            title='Approved Article',
            content='Content',
            author=self.journalist,
            publisher=self.publisher,
            approved=True
        )

    def test_reader_can_view_articles(self):
        """Test that readers can view articles."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_journalist_can_create_article(self):
        """Test that journalists can create articles."""
        self.client.force_authenticate(user=self.journalist)
        data = {
            'title': 'New Article',
            'content': 'New content',
            'publisher': self.publisher.id
        }
        response = self.client.post('/api/articles/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_reader_cannot_create_article(self):
        """Test that readers cannot create articles."""
        self.client.force_authenticate(user=self.reader)
        data = {
            'title': 'New Article',
            'content': 'New content',
            'publisher': self.publisher.id
        }
        response = self.client.post('/api/articles/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access(self):
        """Test that unauthenticated users cannot access API."""
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SubscribedArticlesTest(APITestCase):
    """Test the subscribed articles endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.publisher1 = Publisher.objects.create(name='Tech Daily')
        self.publisher2 = Publisher.objects.create(name='Science Weekly')
        
        self.journalist1 = CustomUser.objects.create_user(
            username='journalist1',
            password='testpass123',
            role='journalist'
        )
        
        self.journalist2 = CustomUser.objects.create_user(
            username='journalist2',
            password='testpass123',
            role='journalist'
        )
        
        self.reader = CustomUser.objects.create_user(
            username='reader1',
            password='testpass123',
            role='reader'
        )
        # Subscribe to publisher1 and journalist1 only
        self.reader.subscribed_publishers.add(self.publisher1)
        self.reader.subscribed_journalists.add(self.journalist1)
        
        # Create articles
        self.article1 = Article.objects.create(
            title='Article from subscribed publisher',
            content='Content 1',
            author=self.journalist1,
            publisher=self.publisher1,
            approved=True
        )
        
        self.article2 = Article.objects.create(
            title='Article from unsubscribed publisher',
            content='Content 2',
            author=self.journalist2,
            publisher=self.publisher2,
            approved=True
        )

    def test_reader_gets_only_subscribed_articles(self):
        """Test that readers only see articles from subscribed sources."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.get('/api/articles/subscribed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return article1 (from subscribed publisher/journalist)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.article1.id)