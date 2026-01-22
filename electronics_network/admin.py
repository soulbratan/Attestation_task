from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from .models import NetworkNode, Product


class ProductAdmin(admin.ModelAdmin):
    """Админ-панель для продуктов."""

    list_display = ("name", "model", "release_date", "network_nodes_count", "created_at")
    list_filter = ("release_date", "created_at")
    search_fields = ("name", "model")
    list_per_page = 20
    ordering = ("-release_date", "name")

    fieldsets = (
        (None, {
            "fields": ("name", "model", "release_date")
        }),
    )

    readonly_fields = ("created_at",)

    def network_nodes_count(self, obj):
        """Количество звеньев, связанных с продуктом."""
        return obj.network_nodes.count()

    network_nodes_count.short_description = _("Количество звеньев")
    network_nodes_count.admin_order_field = "network_nodes__count"


class NetworkNodeAdmin(admin.ModelAdmin):
    """Админ-панель для звеньев сети."""

    # Поля для отображения в списке
    list_display = (
        "name",
        "get_node_type_display",
        "level",
        "city",
        "supplier_name",
        "debt_to_supplier",
        "products_count",
        "created_at"
    )

    # Фильтры
    list_filter = ("node_type", "level", "city", "country", "created_at", "products")

    # Поиск
    search_fields = ("name", "email", "city", "country")

    # Пагинация
    list_per_page = 20

    # Поля в форме редактирования
    fieldsets = (
        (_("Основная информация"), {
            "fields": ("name", "node_type", "email", "supplier", "level")
        }),
        (_("Контактная информация"), {
            "fields": ("country", "city", "street", "house_number"),
        }),
        (_("Продукты"), {
            "fields": ("products",)
        }),
        (_("Финансовая информация"), {
            "fields": ("debt_to_supplier",)
        }),
        (_("Системная информация"), {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )

    # Только для чтения
    readonly_fields = ("level", "created_at")

    # Автозаполнение полей
    autocomplete_fields = ["supplier"]

    # Фильтры в форме
    filter_horizontal = ("products",)

    # Admin actions
    actions = ["clear_debt"]

    def supplier_name(self, obj):
        """Имя поставщика."""
        return obj.supplier.name if obj.supplier else "-"

    supplier_name.short_description = _("Поставщик")
    supplier_name.admin_order_field = "supplier__name"

    def products_count(self, obj):
        """Количество продуктов."""
        return obj.products.count()

    products_count.short_description = _("Продуктов")
    products_count.admin_order_field = "products__count"

    # Admin actions
    def clear_debt(self, request, queryset):
        """Очистить задолженность у выбранных объектов."""
        updated = queryset.update(debt_to_supplier=Decimal("0.00"))
        self.message_user(
            request,
            f"Задолженность очищена у {updated} объектов."
        )

    clear_debt.short_description = "Очистить задолженность перед поставщиком"

    def get_queryset(self, request):
        """Оптимизация запросов."""
        return super().get_queryset(request).select_related("supplier").prefetch_related("products")

    def get_readonly_fields(self, request, obj=None):
        """Настройка readonly полей в зависимости от состояния объекта."""
        readonly_fields = list(self.readonly_fields)

        if obj and obj.node_type == NetworkNode.NodeType.FACTORY:
            # Для завода нельзя менять поставщика
            readonly_fields.append("supplier")

        return readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        """Добавляем help_text для полей."""
        form = super().get_form(request, obj, **kwargs)

        # Добавляем подсказки для полей
        if "debt_to_supplier" in form.base_fields:
            form.base_fields["debt_to_supplier"].help_text = _(
                "Задолженность в рублях с точностью до копеек. "
                "У завода всегда должна быть 0."
            )

        if "supplier" in form.base_fields:
            form.base_fields["supplier"].help_text = _(
                "Предыдущее звено в цепочке поставок. "
                "Завод не должен иметь поставщика."
            )

        if "email" in form.base_fields:
            form.base_fields["email"].help_text = _(
                "Уникальный email адрес звена сети."
            )

        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Ограничение выбора поставщика."""
        if db_field.name == "supplier":
            # Исключаем текущий объект из возможных поставщиков
            if request.resolver_match.kwargs.get("object_id"):
                kwargs["queryset"] = NetworkNode.objects.exclude(
                    id=request.resolver_match.kwargs["object_id"]
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Регистрируем модели в админке
admin.site.register(Product, ProductAdmin)
admin.site.register(NetworkNode, NetworkNodeAdmin)
