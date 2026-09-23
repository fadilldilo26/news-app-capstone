from rest_framework import serializers
from .models import CustomUser, Publisher, Article, Newsletter


class UserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser model."""
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'subscribed_publishers', 
                  'subscribed_journalists']
        read_only_fields = ['id']


class PublisherSerializer(serializers.ModelSerializer):
    """Serializer for Publisher model."""
    
    class Meta:
        model = Publisher
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for Article model."""
    author_name = serializers.CharField(source='author.username', read_only=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True)
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author', 'author_name', 
                  'publisher', 'publisher_name', 'created_at', 'updated_at', 'approved']
        read_only_fields = ['id', 'created_at', 'updated_at', 'author']
    
    def validate(self, data):
        """Ensure article has either a journalist author or publisher."""
        if not data.get('author') and not data.get('publisher'):
            raise serializers.ValidationError(
                "Article must have either an author (journalist) or a publisher."
            )
        return data


class NewsletterSerializer(serializers.ModelSerializer):
    """Serializer for Newsletter model."""
    author_name = serializers.CharField(source='author.username', read_only=True)
    articles_list = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Newsletter
        fields = ['id', 'title', 'description', 'author', 'author_name', 
                  'articles', 'articles_list', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'author']