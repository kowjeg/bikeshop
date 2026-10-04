from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    # HiddenField подставляет текущего пользователя и даёт DRF проверить
    # UniqueConstraint(product, user) до записи в базу -> 400 вместо 500
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    username = serializers.StringRelatedField(source='user', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'username', 'rating', 'comments', 'created_at']
        read_only_fields = ['created_at']
