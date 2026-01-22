from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Product(models.Model):
    """
    Модель продукта/оборудования.
    Один продукт может быть у нескольких поставщиков.
    """

    name = models.CharField(_("название продукта"), max_length=255, help_text=_("Название продукта/оборудования"))

    model = models.CharField(_("модель продукта"), max_length=255, help_text=_("Модель продукта"))

    release_date = models.DateField(_("дата выхода продукта"), help_text=_("Дата выхода продукта на рынок"))

    created_at = models.DateTimeField(_("время создания"), auto_now_add=True)

    class Meta:
        verbose_name = _("продукт")
        verbose_name_plural = _("продукты")
        ordering = ["-release_date", "name"]
        unique_together = ["name", "model"]  # Уникальная комбинация имя+модель

    def __str__(self):
        return f"{self.name} ({self.model})"

    @property
    def full_name(self):
        """Полное название продукта с моделью."""
        return f"{self.name} {self.model}"


class NetworkNode(models.Model):
    """
    Модель для представления звена сети по продаже электроники.
    Иерархия: Завод → Розничная сеть → Индивидуальный предприниматель
    """

    class NodeType(models.TextChoices):
        FACTORY = "factory", _("Завод")
        RETAIL = "retail", _("Розничная сеть")
        INDIVIDUAL = "individual", _("Индивидуальный предприниматель")

    # Основная информация
    name = models.CharField(_("название"), max_length=255, unique=True, help_text=_("Название звена сети"))

    node_type = models.CharField(
        _("тип звена"),
        max_length=20,
        choices=NodeType.choices,
        default=NodeType.FACTORY,
        help_text=_("Тип звена в сети"),
    )

    # Контактная информация
    email = models.EmailField(
        _("email"),
        max_length=255,
        unique=True,  # ✅ Email должен быть уникальным
        validators=[EmailValidator()],
        help_text=_("Контактный email"),
    )

    country = models.CharField(_("страна"), max_length=100, help_text=_("Страна расположения"))

    city = models.CharField(_("город"), max_length=100, help_text=_("Город расположения"))

    street = models.CharField(_("улица"), max_length=255, help_text=_("Улица расположения"))

    house_number = models.CharField(_("номер дома"), max_length=20, help_text=_("Номер дома/строения"))

    # Иерархические связи
    supplier = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients",
        verbose_name=_("поставщик"),
        help_text=_("Поставщик оборудования (предыдущее звено в цепочке)"),
    )

    # Связь с продуктами (ManyToMany)
    products = models.ManyToManyField(
        Product,
        related_name="network_nodes",
        verbose_name=_("продукты"),
        help_text=_("Продукты, которые поставляет это звено"),
    )

    # Финансовая информация
    debt_to_supplier = models.DecimalField(
        _("задолженность перед поставщиком"),
        max_digits=12,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text=_("Задолженность в денежном выражении (до копеек)"),
    )

    # Системные поля
    created_at = models.DateTimeField(_("время создания"), auto_now_add=True, help_text=_("Время создания записи"))

    level = models.IntegerField(
        _("уровень в иерархии"), default=0, editable=False, help_text=_("Уровень в иерархии сети (0 - завод)")
    )

    class Meta:
        verbose_name = _("звено сети")
        verbose_name_plural = _("звенья сети")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["supplier"]),
            models.Index(fields=["level"]),
            models.Index(fields=["city"]),
            models.Index(fields=["country"]),
            models.Index(fields=["debt_to_supplier"]),
            models.Index(fields=["email"]),  # Индекс для уникального email
        ]

    def __str__(self):
        return f"{self.get_node_type_display()}: {self.name} ({self.city})"

    def save(self, *args, **kwargs):
        """Автоматически вычисляем уровень в иерархии перед сохранением."""
        if self.supplier:
            self.level = self.supplier.level + 1
        else:
            self.level = 0  # Завод

        # Проверка бизнес-логики
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Валидация бизнес-логики."""
        super().clean()

        # 1. Завод не может иметь поставщика
        if self.node_type == self.NodeType.FACTORY and self.supplier:
            raise ValidationError({"supplier": _("Завод не может иметь поставщика.")})

        # 2. Завод всегда должен быть на уровне 0
        if self.node_type == self.NodeType.FACTORY and self.supplier is None and self.level != 0:
            raise ValidationError(_("Завод должен быть на уровне 0."))

        # 3. Нельзя быть своим собственным поставщиком
        if self.supplier and self.supplier == self:
            raise ValidationError({"supplier": _("Звено не может быть своим собственным поставщиком.")})

        # 4. Проверка циклических ссылок
        if self.supplier:
            current = self.supplier
            visited = {self.id} if self.id else set()
            while current:
                if current.id in visited:
                    raise ValidationError({"supplier": _("Обнаружена циклическая ссылка в цепочке поставщиков.")})
                if current.id:
                    visited.add(current.id)
                current = current.supplier

        # 5. Максимальный уровень иерархии
        max_level = 10
        if self.level > max_level:
            raise ValidationError(_("Превышен максимальный уровень иерархии (%(max)s)."), params={"max": max_level})

        # 6. Завод не может иметь задолженность
        if self.node_type == self.NodeType.FACTORY and self.debt_to_supplier > 0:
            raise ValidationError({"debt_to_supplier": _("Завод не может иметь задолженность перед поставщиком.")})

    def get_full_address(self):
        """Полный адрес звена."""
        return f"{self.country}, {self.city}, {self.street}, д. {self.house_number}"

    def get_hierarchy_path(self):
        """Путь в иерархии от завода до текущего звена."""
        path = []
        current = self

        while current:
            path.insert(0, current.name)
            current = current.supplier

        return " → ".join(path) if path else self.name

    @property
    def is_factory(self):
        """Является ли звено заводом."""
        return self.node_type == self.NodeType.FACTORY

    @property
    def supplier_name(self):
        """Имя поставщика (для удобного отображения)."""
        return self.supplier.name if self.supplier else "-"

    @property
    def products_list(self):
        """Список продуктов в читаемом формате."""
        return ", ".join(str(product) for product in self.products.all())
