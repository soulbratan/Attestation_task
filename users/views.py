from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from .models import User
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer
from .permissions import IsActiveEmployee


class UserRegistrationView(generics.CreateAPIView):
    """Регистрация нового пользователя."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Возвращаем информацию о пользователе
            user_data = UserSerializer(user).data
            return Response({
                'user': user_data,
                'message': 'Регистрация успешна. Ожидайте активации администратором.'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """Вход пользователя и получение JWT токенов."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Создаем JWT токены
            refresh = RefreshToken.for_user(user)

            # Опционально: выполняем логин (для сессий)
            login(request, user)

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Получение и обновление профиля пользователя."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsActiveEmployee]

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    """Список активных сотрудников (только для администраторов)."""
    queryset = User.objects.filter(is_active_employee=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]