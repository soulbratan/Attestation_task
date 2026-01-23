from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Менеджер для кастомной модели пользователя с email в качестве username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Создает и сохраняет пользователя с email и паролем."""
        if not email:
            raise ValueError("Email должен быть указан")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Создает обычного пользователя."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Создает суперпользователя."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active_employee", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("У суперпользователя должен быть параметр is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Необходимо установить параметр is_superuser=True для суперпользователя")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Кастомная модель пользователя.
    Используем email в качестве уникального идентификатора.
    """

    username = None
    email = models.EmailField(_("email address"), unique=True)
    is_active_employee = models.BooleanField(
        _("active employee"),
        default=False,
        help_text=_("Указать, является ли данный пользователь действующим сотрудником с доступом к API"),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["email"]

    def __str__(self):
        return self.email
