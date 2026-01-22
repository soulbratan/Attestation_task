from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTests(TestCase):
    """Тесты для модели User."""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Тест',
            'last_name': 'Пользователь'
        }

    def test_create_user(self):
        """Тест создания обычного пользователя."""
        user = User.objects.create_user(**self.user_data)

        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Тест')
        self.assertEqual(user.last_name, 'Пользователь')
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_active_employee)
        self.assertTrue(user.check_password('testpass123'))

    def test_create_superuser(self):
        """Тест создания суперпользователя."""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )

        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_active_employee)

    def test_email_unique(self):
        """Тест уникальности email."""
        User.objects.create_user(email='test@example.com', password='pass123')

        with self.assertRaises(Exception):
            User.objects.create_user(email='test@example.com', password='pass456')

    def test_string_representation(self):
        """Тест строкового представления."""
        user = User.objects.create_user(email='test@example.com', password='pass123')
        self.assertEqual(str(user), 'test@example.com')


class UserAPITests(APITestCase):
    """Тесты для API пользователей."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.profile_url = reverse('profile')

        # Создаем активного пользователя
        self.active_user = User.objects.create_user(
            email='active@example.com',
            password='testpass123',
            first_name='Активный',
            last_name='Сотрудник',
            is_active_employee=True
        )

        # Создаем неактивного пользователя
        self.inactive_user = User.objects.create_user(
            email='inactive@example.com',
            password='testpass123',
            first_name='Неактивный',
            last_name='Сотрудник',
            is_active_employee=False
        )

    def test_user_registration(self):
        """Тест регистрации пользователя."""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password2': 'newpass123',
            'first_name': 'Новый',
            'last_name': 'Пользователь'
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('message', response.data)

        # Проверяем, что пользователь создан
        user = User.objects.get(email='newuser@example.com')
        self.assertEqual(user.first_name, 'Новый')
        self.assertFalse(user.is_active_employee)  # Должен быть неактивным по умолчанию

    def test_user_registration_password_mismatch(self):
        """Тест регистрации с несовпадающими паролями."""
        data = {
            'email': 'newuser@example.com',
            'password': 'pass123',
            'password2': 'pass456',  # Не совпадает
            'first_name': 'Новый',
            'last_name': 'Пользователь'
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password2', response.data)

    def test_user_login_success(self):
        """Тест успешного входа."""
        data = {
            'email': 'active@example.com',
            'password': 'testpass123'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_user_login_inactive_employee(self):
        """Тест входа неактивного сотрудника."""
        data = {
            'email': 'inactive@example.com',
            'password': 'testpass123'
        }

        response = self.client.post(self.login_url, data, format='json')

        # Должен успешно войти, но не будет иметь доступ к API
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_user_login_invalid_credentials(self):
        """Тест входа с неверными данными."""
        data = {
            'email': 'active@example.com',
            'password': 'wrongpassword'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_profile_authenticated(self):
        """Тест получения профиля аутентифицированным пользователем."""
        self.client.force_authenticate(user=self.active_user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'active@example.com')
        self.assertEqual(response.data['first_name'], 'Активный')

    def test_get_profile_unauthenticated(self):
        """Тест получения профиля без аутентификации."""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        """Тест обновления профиля."""
        self.client.force_authenticate(user=self.active_user)

        data = {
            'first_name': 'Обновленное',
            'last_name': 'Имя'
        }

        response = self.client.patch(self.profile_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Обновленное')
        self.assertEqual(response.data['last_name'], 'Имя')

        # Проверяем в базе
        self.active_user.refresh_from_db()
        self.assertEqual(self.active_user.first_name, 'Обновленное')


class PermissionTests(TestCase):
    """Тесты для разрешений."""

    def setUp(self):
        from users.permissions import IsActiveEmployee

        self.permission = IsActiveEmployee()

        # Создаем разные типы пользователей
        self.active_user = User.objects.create_user(
            email='active@example.com',
            password='pass123',
            is_active_employee=True
        )

        self.inactive_user = User.objects.create_user(
            email='inactive@example.com',
            password='pass123',
            is_active_employee=False
        )

    def test_is_active_employee_permission_active(self):
        """Тест разрешения для активного сотрудника."""
        request = type('Request', (), {'user': self.active_user})()

        self.assertTrue(self.permission.has_permission(request, None))

    def test_is_active_employee_permission_inactive(self):
        """Тест разрешения для неактивного сотрудника."""
        request = type('Request', (), {'user': self.inactive_user})()

        self.assertFalse(self.permission.has_permission(request, None))

    def test_is_active_employee_permission_no_user(self):
        """Тест разрешения без пользователя."""
        request = type('Request', (), {'user': None})()

        self.assertFalse(self.permission.has_permission(request, None))