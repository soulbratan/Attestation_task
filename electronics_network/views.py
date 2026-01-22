from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count
from .models import NetworkNode, Product
from .serializers import (
    NetworkNodeSerializer,
    NetworkNodeCreateSerializer,
    NetworkNodeUpdateSerializer,
    ProductSerializer
)
from .filters import NetworkNodeFilter
from users.permissions import IsActiveEmployee


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для продуктов."""

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsActiveEmployee]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'model']
    ordering_fields = ['name', 'model', 'release_date', 'created_at']
    ordering = ['-release_date']

    @action(detail=True, methods=['get'])
    def network_nodes(self, request, pk=None):
        """Получить все звенья, связанные с продуктом."""
        product = self.get_object()
        nodes = product.network_nodes.all()
        page = self.paginate_queryset(nodes)

        if page is not None:
            serializer = NetworkNodeSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NetworkNodeSerializer(nodes, many=True)
        return Response(serializer.data)


class NetworkNodeViewSet(viewsets.ModelViewSet):
    """ViewSet для звеньев сети."""

    queryset = NetworkNode.objects.all()
    permission_classes = [IsAuthenticated, IsActiveEmployee]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NetworkNodeFilter
    search_fields = ['name', 'email', 'city', 'country', 'street']
    ordering_fields = ['name', 'level', 'city', 'debt_to_supplier', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action == 'create':
            return NetworkNodeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NetworkNodeUpdateSerializer
        return NetworkNodeSerializer

    def get_queryset(self):
        """Оптимизация запросов и дополнительные фильтры."""
        queryset = super().get_queryset()

        # Дополнительная фильтрация по параметрам запроса
        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(country__iexact=country)

        return queryset.select_related('supplier').prefetch_related('products')

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика по сети."""
        total_nodes = NetworkNode.objects.count()
        factories = NetworkNode.objects.filter(node_type=NetworkNode.NodeType.FACTORY).count()
        retail = NetworkNode.objects.filter(node_type=NetworkNode.NodeType.RETAIL).count()
        individual = NetworkNode.objects.filter(node_type=NetworkNode.NodeType.INDIVIDUAL).count()

        total_debt = NetworkNode.objects.aggregate(
            total_debt=Sum('debt_to_supplier')
        )['total_debt'] or 0

        cities = NetworkNode.objects.values('city').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        return Response({
            'total_nodes': total_nodes,
            'factories': factories,
            'retail_networks': retail,
            'individual_entrepreneurs': individual,
            'total_debt': float(total_debt),
            'top_cities': list(cities)
        })

    @action(detail=True, methods=['post'])
    def clear_debt(self, request, pk=None):
        """Очистить задолженность у конкретного звена."""
        node = self.get_object()
        node.debt_to_supplier = 0
        node.save()

        serializer = self.get_serializer(node)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_clear_debt(self, request):
        """Массовая очистка задолженности."""
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': 'Не указаны ID звеньев.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated = NetworkNode.objects.filter(id__in=ids).update(debt_to_supplier=0)

        return Response({
            'message': f'Задолженность очищена у {updated} звеньев.',
            'updated_count': updated
        })

    @action(detail=True, methods=['get'])
    def hierarchy(self, request, pk=None):
        """Получить иерархию от текущего звена вверх и вниз."""
        node = self.get_object()

        # Иерархия вверх (поставщики)
        suppliers_hierarchy = []
        current = node.supplier
        while current:
            suppliers_hierarchy.append({
                'id': current.id,
                'name': current.name,
                'type': current.get_node_type_display(),
                'level': current.level
            })
            current = current.supplier

        # Иерархия вниз (клиенты)
        clients_hierarchy = []
        clients = node.clients.all()
        for client in clients:
            clients_hierarchy.append({
                'id': client.id,
                'name': client.name,
                'type': client.get_node_type_display(),
                'level': client.level
            })

        return Response({
            'current_node': {
                'id': node.id,
                'name': node.name,
                'type': node.get_node_type_display(),
                'level': node.level
            },
            'suppliers_hierarchy': suppliers_hierarchy,
            'clients_hierarchy': clients_hierarchy
        })

    @action(detail=False, methods=['get'])
    def countries(self, request):
        """Получить список всех стран."""
        countries = NetworkNode.objects.values_list('country', flat=True).distinct().order_by('country')
        return Response(list(countries))

    @action(detail=False, methods=['get'])
    def cities(self, request):
        """Получить список всех городов."""
        country = request.query_params.get('country', None)
        queryset = NetworkNode.objects.all()

        if country:
            queryset = queryset.filter(country__iexact=country)

        cities = queryset.values_list('city', flat=True).distinct().order_by('city')
        return Response(list(cities))