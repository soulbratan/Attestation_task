from django_filters import rest_framework as filters
from .models import NetworkNode


class NetworkNodeFilter(filters.FilterSet):
    """Фильтры для звеньев сети."""

    country = filters.CharFilter(field_name="country", lookup_expr="iexact")
    city = filters.CharFilter(field_name="city", lookup_expr="icontains")
    min_debt = filters.NumberFilter(field_name="debt_to_supplier", lookup_expr="gte")
    max_debt = filters.NumberFilter(field_name="debt_to_supplier", lookup_expr="lte")
    node_type = filters.CharFilter(field_name="node_type", lookup_expr="exact")
    has_supplier = filters.BooleanFilter(field_name="supplier", lookup_expr="isnull", exclude=True)
    supplier_name = filters.CharFilter(field_name="supplier__name", lookup_expr="icontains")
    product_name = filters.CharFilter(field_name="products__name", lookup_expr="icontains")

    class Meta:
        model = NetworkNode
        fields = {
            "name": ["icontains"],
            "email": ["icontains"],
            "level": ["exact", "gte", "lte"],
            "created_at": ["gte", "lte", "exact"],
        }

    @property
    def qs(self):
        """Оптимизация запросов."""
        queryset = super().qs
        return queryset.select_related("supplier").prefetch_related("products")
