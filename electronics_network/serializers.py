from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import NetworkNode, Product


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для продукта."""

    class Meta:
        model = Product
        fields = ('id', 'name', 'model', 'release_date', 'created_at')
        read_only_fields = ('id', 'created_at')


class NetworkNodeSerializer(serializers.ModelSerializer):
    """Сериализатор для звена сети."""

    products = ProductSerializer(many=True, read_only=True)
    product_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Product.objects.all(),
        write_only=True,
        source='products',
        required=False
    )

    supplier_name = serializers.CharField(
        source='supplier.name',
        read_only=True,
        allow_null=True
    )

    node_type_display = serializers.CharField(
        source='get_node_type_display',
        read_only=True
    )

    full_address = serializers.CharField(
        source='get_full_address',
        read_only=True
    )

    hierarchy_path = serializers.CharField(
        source='get_hierarchy_path',
        read_only=True
    )

    class Meta:
        model = NetworkNode
        fields = (
            'id',
            'name',
            'node_type',
            'node_type_display',
            'email',
            'country',
            'city',
            'street',
            'house_number',
            'full_address',
            'supplier',
            'supplier_name',
            'products',
            'product_ids',
            'debt_to_supplier',
            'level',
            'hierarchy_path',
            'created_at'
        )
        read_only_fields = ('id', 'level', 'created_at', 'node_type_display', 'full_address', 'hierarchy_path')

    def validate(self, data):
        """Валидация бизнес-логики."""
        # Получаем тип звена из данных или из инстанса
        node_type = data.get('node_type', getattr(self.instance, 'node_type', None))
        supplier = data.get('supplier', getattr(self.instance, 'supplier', None))
        debt_to_supplier = data.get('debt_to_supplier', getattr(self.instance, 'debt_to_supplier', 0))

        # Проверка: завод не может иметь поставщика
        if node_type == NetworkNode.NodeType.FACTORY and supplier:
            raise serializers.ValidationError({
                'supplier': _('Завод не может иметь поставщика.')
            })

        # Проверка: завод не может иметь задолженность
        if node_type == NetworkNode.NodeType.FACTORY and debt_to_supplier > 0:
            raise serializers.ValidationError({
                'debt_to_supplier': _('Завод не может иметь задолженность перед поставщиком.')
            })

        # Проверка: нельзя быть своим собственным поставщиком
        if supplier and self.instance and supplier.id == self.instance.id:
            raise serializers.ValidationError({
                'supplier': _('Звено не может быть своим собственным поставщиком.')
            })

        return data

    def create(self, validated_data):
        """Создание звена с автоматическим расчетом уровня."""
        # Извлекаем продукты (если есть)
        products = validated_data.pop('products', [])

        # Создаем звено
        instance = super().create(validated_data)

        # Добавляем продукты
        if products:
            instance.products.set(products)

        return instance

    def update(self, instance, validated_data):
        """Обновление звена с валидацией."""
        # Извлекаем продукты (если есть)
        products = validated_data.pop('products', [])

        # Обновляем звено
        instance = super().update(instance, validated_data)

        # Обновляем продукты если они переданы
        if 'products' in self.initial_data:
            instance.products.set(products)

        return instance


class NetworkNodeCreateSerializer(NetworkNodeSerializer):
    """Сериализатор для создания звена (без read-only полей)."""

    class Meta(NetworkNodeSerializer.Meta):
        read_only_fields = ('id', 'level', 'created_at')


class NetworkNodeUpdateSerializer(NetworkNodeSerializer):
    """Сериализатор для обновления звена (запрет обновления задолженности)."""

    class Meta(NetworkNodeSerializer.Meta):
        read_only_fields = NetworkNodeSerializer.Meta.read_only_fields + ('debt_to_supplier',)