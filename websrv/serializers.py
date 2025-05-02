from rest_framework import serializers
from .models import User
from .models import Comment
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    expertise_tag = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'bill',
            'text',
            'user_name',
            'auth0_id',
            'expertise_tags',
            'likes',
            'dislikes',
            'created_at',
            'updated_at',
        ]

  