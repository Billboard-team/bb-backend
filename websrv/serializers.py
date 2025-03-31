from rest_framework import serializers
from .models import User, Bill, Comment

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'bill', 'text', 'user_name', 'likes', 'dislikes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Include password in creation but not in serialized output
        password = self.context['request'].data.get('password')
        comment = Comment.objects.create(**validated_data, password=password)
        return comment
