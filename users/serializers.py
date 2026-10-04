from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers


User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def validate_username(self, value):
        # сайт (users/views.py login_view) ищет логин в нижнем регистре,
        # поэтому и здесь сохраняем его так же, как RegisterForm
        value = value.lower()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate(self, attrs):
        # стандартные проверки Django: длина, простые пароли, только цифры,
        # схожесть с логином и email (для этого нужен user)
        user = User(username=attrs['username'], email=attrs['email'])
        try:
            password_validation.validate_password(attrs['password'], user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return attrs

    def create(self, validated_data):
        # create_user хеширует пароль, а objects.create сохранил бы его как есть
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
