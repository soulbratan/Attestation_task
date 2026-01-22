from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomUserAdmin(UserAdmin):
    """Админ-панель для кастомной модели пользователя."""

    # Поля для отображения в списке
    list_display = ("email", "first_name", "last_name", "is_active_employee", "is_staff", "is_superuser", "date_joined")

    # Фильтры
    list_filter = ("is_active_employee", "is_staff", "is_superuser", "date_joined")

    # Поиск
    search_fields = ("email", "first_name", "last_name")

    # Сортировка
    ordering = ("email",)

    # Порядок полей в форме редактирования
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (_("Permissions"), {
            "fields": ("is_active_employee", "is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        (_("Important dates"), {
            "fields": ("last_login", "date_joined"),
            "classes": ("collapse",),  # Сворачиваемый раздел
        }),
    )

    # Поля при добавлении пользователя
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "first_name", "last_name"),
        }),
        (_("Permissions"), {
            "fields": ("is_active_employee", "is_staff", "is_superuser"),
        }),
    )

    # Делаем поля только для чтения
    readonly_fields = ("last_login", "date_joined")

    # Admin action для активации сотрудников
    actions = ["activate_employees", "deactivate_employees"]

    def activate_employees(self, request, queryset):
        """Активировать выбранных сотрудников."""
        updated = queryset.update(is_active_employee=True)
        self.message_user(request, f"Активировано {updated} сотрудников.")

    activate_employees.short_description = "Активировать выбранных сотрудников"

    def deactivate_employees(self, request, queryset):
        """Деактивировать выбранных сотрудников."""
        updated = queryset.update(is_active_employee=False)
        self.message_user(request, f"Деактивировано {updated} сотрудников.")

    deactivate_employees.short_description = "Деактивировать выбранных сотрудников"

    def get_queryset(self, request):
        """Показываем всех пользователей, но суперпользователь видит всех."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(is_active_employee=True)

    def get_list_display(self, request):
        """Возвращаем разные наборы полей для разных пользователей."""
        # Базовый набор полей
        list_display = list(self.list_display)

        # Для не-суперпользователей убираем is_staff и is_superuser из отображения
        if not request.user.is_superuser:
            list_display = [field for field in list_display if field not in ("is_staff", "is_superuser")]

        return list_display

    def get_list_editable(self, request):
        """Определяем, какие поля можно редактировать."""
        # Только суперпользователь может редактировать прямо из таблицы
        if request.user.is_superuser:
            return self.list_editable
        return ()

    def get_form(self, request, obj=None, **kwargs):
        """Добавляем help_text для полей."""
        form = super().get_form(request, obj, **kwargs)

        # Добавляем подсказки для полей
        if "last_login" in form.base_fields:
            form.base_fields["last_login"].help_text = "Дата последнего входа пользователя"
        if "date_joined" in form.base_fields:
            form.base_fields["date_joined"].help_text = "Дата регистрации пользователя"
        if "is_active_employee" in form.base_fields:
            form.base_fields["is_active_employee"].help_text = _(
                "Определяет, имеет ли пользователь доступ к API. "
                "Только активные сотрудники могут использовать API."
            )

        return form

    def changelist_view(self, request, extra_context=None):
        """Добавляем контекст для отображения подсказки."""
        extra_context = extra_context or {}
        extra_context["title"] = "Пользователи"
        extra_context["subtitle"] = "Дважды кликните на статусе сотрудника для быстрого изменения"

        return super().changelist_view(request, extra_context=extra_context)


admin.site.register(User, CustomUserAdmin)

admin.site.site_header = "Управление сетью электроники"
admin.site.site_title = "Админ-панель сети электроники"
admin.site.index_title = "Панель управления"