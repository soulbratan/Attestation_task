from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        validators=[validate_password]
    )
    password2 = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ("email", "password", "password2", "first_name", "last_name")

    def validate(self, data):
        """Проверяем, что пароли совпадают."""
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Пароли не совпадают."})
        return data

    def create(self, validated_data):
        # Удаляем поле password2, так как оно не нужно для создания пользователя
        validated_data.pop("password2")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            is_active_employee=False  # По умолчанию не активный сотрудник
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для входа пользователя."""
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"}
    )

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if email and password:
            user = authenticate(username=email, password=password)

            if user:
                if not user.is_active:
                    raise serializers.ValidationError("Пользователь неактивен.")
                data["user"] = user
            else:
                raise serializers.ValidationError("Неверные учетные данные.")
        else:
            raise serializers.ValidationError("Необходимо указать email и пароль.")

        return data


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о пользователе."""

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "is_active_employee", "date_joined")
        read_only_fields = ("id", "is_active_employee", "date_joined")