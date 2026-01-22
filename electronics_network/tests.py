from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Product, NetworkNode
from datetime import date, timedelta

User = get_user_model()


class ProductModelTests(TestCase):
    """Тесты для модели Product."""

    def setUp(self):
        self.product_data = {
            'name': 'Смартфон',
            'model': 'X-Phone Pro',
            'release_date': date.today() - timedelta(days=30)
        }

    def test_create_product(self):
        """Тест создания продукта."""
        product = Product.objects.create(**self.product_data)

        self.assertEqual(product.name, 'Смартфон')
        self.assertEqual(product.model, 'X-Phone Pro')
        self.assertEqual(str(product), 'Смартфон (X-Phone Pro)')

    def test_unique_name_model(self):
        """Тест уникальности комбинации имя+модель."""
        Product.objects.create(**self.product_data)

        with self.assertRaises(Exception):
            Product.objects.create(**self.product_data)

    def test_product_full_name(self):
        """Тест свойства full_name."""
        product = Product.objects.create(**self.product_data)

        self.assertEqual(product.full_name, 'Смартфон X-Phone Pro')


class NetworkNodeModelTests(TestCase):
    """Тесты для модели NetworkNode."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_active_employee=True
        )

        # Создаем продукты
        self.product1 = Product.objects.create(
            name='Ноутбук',
            model='UltraBook Z',
            release_date=date.today() - timedelta(days=60)
        )

        self.product2 = Product.objects.create(
            name='Планшет',
            model='TabMaster 10',
            release_date=date.today() - timedelta(days=90)
        )

    def test_create_factory(self):
        """Тест создания завода."""
        factory = NetworkNode.objects.create(
            name='Электротехнический завод "Восток"',
            node_type=NetworkNode.NodeType.FACTORY,
            email='factory@example.com',
            country='Россия',
            city='Новосибирск',
            street='Промышленная',
            house_number='15А'
        )

        self.assertEqual(factory.name, 'Электротехнический завод "Восток"')
        self.assertEqual(factory.node_type, NetworkNode.NodeType.FACTORY)
        self.assertEqual(factory.level, 0)  # Завод должен быть на уровне 0
        self.assertIsNone(factory.supplier)  # Завод не должен иметь поставщика
        self.assertEqual(factory.debt_to_supplier, 0)  # Завод не должен иметь долг

    def test_create_retail_with_supplier(self):
        """Тест создания розничной сети с поставщиком."""
        # Создаем завод
        factory = NetworkNode.objects.create(
            name='Завод',
            node_type=NetworkNode.NodeType.FACTORY,
            email='factory@example.com',
            country='Россия',
            city='Москва',
            street='Заводская',
            house_number='1'
        )

        # Создаем розничную сеть
        retail = NetworkNode.objects.create(
            name='Розничная сеть',
            node_type=NetworkNode.NodeType.RETAIL,
            email='retail@example.com',
            country='Россия',
            city='Москва',
            street='Тверская',
            house_number='25',
            supplier=factory,
            debt_to_supplier=50000.00
        )

        self.assertEqual(retail.node_type, NetworkNode.NodeType.RETAIL)
        self.assertEqual(retail.supplier, factory)
        self.assertEqual(retail.level, 1)  # На уровень выше завода
        self.assertEqual(retail.debt_to_supplier, 50000.00)

    def test_factory_cannot_have_supplier(self):
        """Тест: завод не может иметь поставщика."""
        factory1 = NetworkNode.objects.create(
            name='Завод 1',
            node_type=NetworkNode.NodeType.FACTORY,
            email='factory1@example.com',
            country='Россия',
            city='Москва',
            street='Заводская',
            house_number='1'
        )

        # Пытаемся создать завод с поставщиком
        with self.assertRaises(Exception):
            NetworkNode.objects.create(
                name='Завод 2',
                node_type=NetworkNode.NodeType.FACTORY,
                email='factory2@example.com',
                country='Россия',
                city='Санкт-Петербург',
                street='Заводская',
                house_number='2',
                supplier=factory1  # Не должно быть разрешено
            )

    def test_factory_cannot_have_debt(self):
        """Тест: завод не может иметь задолженность."""
        with self.assertRaises(Exception):
            NetworkNode.objects.create(
                name='Завод',
                node_type=NetworkNode.NodeType.FACTORY,
                email='factory@example.com',
                country='Россия',
                city='Москва',
                street='Заводская',
                house_number='1',
                debt_to_supplier=10000.00  # Не должно быть разрешено
            )

    def test_full_address_property(self):
        """Тест свойства full_address."""
        node = NetworkNode.objects.create(
            name='Тестовое звено',
            node_type=NetworkNode.NodeType.RETAIL,
            email='test@example.com',
            country='Россия',
            city='Москва',
            street='Тверская',
            house_number='25'
        )

        expected_address = 'Россия, Москва, Тверская, д. 25'
        self.assertEqual(node.get_full_address(), expected_address)

    def test_add_products_to_node(self):
        """Тест добавления продуктов к звену сети."""
        node = NetworkNode.objects.create(
            name='Розничная сеть',
            node_type=NetworkNode.NodeType.RETAIL,
            email='retail@example.com',
            country='Россия',
            city='Москва',
            street='Тверская',
            house_number='25'
        )

        # Добавляем продукты
        node.products.add(self.product1, self.product2)

        self.assertEqual(node.products.count(), 2)
        self.assertIn(self.product1, node.products.all())
        self.assertIn(self.product2, node.products.all())

    def test_hierarchy_path(self):
        """Тест свойства hierarchy_path."""
        factory = NetworkNode.objects.create(
            name='Завод',
            node_type=NetworkNode.NodeType.FACTORY,
            email='factory@example.com',
            country='Россия',
            city='Москва',
            street='Заводская',
            house_number='1'
        )

        retail = NetworkNode.objects.create(
            name='Розничная сеть',
            node_type=NetworkNode.NodeType.RETAIL,
            email='retail@example.com',
            country='Россия',
            city='Москва',
            street='Тверская',
            house_number='25',
            supplier=factory
        )

        ip = NetworkNode.objects.create(
            name='ИП Иванов',
            node_type=NetworkNode.NodeType.INDIVIDUAL,
            email='ip@example.com',
            country='Россия',
            city='Москва',
            street='Арбат',
            house_number='15',
            supplier=retail
        )

        self.assertEqual(ip.get_hierarchy_path(), 'Завод → Розничная сеть → ИП Иванов')
        self.assertEqual(factory.get_hierarchy_path(), 'Завод')


class ProductAPITests(APITestCase):
    """Тесты для API продуктов."""

    def setUp(self):
        self.client = APIClient()

        # Создаем активного пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_active_employee=True
        )

        self.client.force_authenticate(user=self.user)

        # Создаем тестовые продукты
        self.product1 = Product.objects.create(
            name='Смартфон',
            model='X-Phone Pro',
            release_date=date.today() - timedelta(days=30)
        )

        self.product2 = Product.objects.create(
            name='Ноутбук',
            model='UltraBook Z',
            release_date=date.today() - timedelta(days=60)
        )

        self.product_list_url = reverse('product-list')
        self.product_detail_url = reverse('product-detail', args=[self.product1.id])

    def test_get_products_list(self):
        """Тест получения списка продуктов."""
        response = self.client.get(self.product_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results'] if 'results' in response.data else response.data), 2)

    def test_create_product(self):
        """Тест создания продукта."""
        data = {
            'name': 'Планшет',
            'model': 'TabMaster 10',
            'release_date': date.today().isoformat()
        }

        response = self.client.post(self.product_list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Планшет')
        self.assertEqual(Product.objects.count(), 3)

    def test_get_product_detail(self):
        """Тест получения деталей продукта."""
        response = self.client.get(self.product_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Смартфон')
        self.assertEqual(response.data['model'], 'X-Phone Pro')

    def test_update_product(self):
        """Тест обновления продукта."""
        data = {
            'name': 'Обновленный смартфон',
            'model': 'X-Phone Pro Max'
        }

        response = self.client.patch(self.product_detail_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Обновленный смартфон')

        # Проверяем в базе
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.name, 'Обновленный смартфон')

    def test_delete_product(self):
        """Тест удаления продукта."""
        response = self.client.delete(self.product_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 1)  # Должен остаться только product2
        self.assertFalse(Product.objects.filter(id=self.product1.id).exists())

    def test_search_products(self):
        """Тест поиска продуктов."""
        response = self.client.get(self.product_list_url, {'search': 'смартфон'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Смартфон')


class NetworkNodeAPITests(APITestCase):
    """Тесты для API звеньев сети."""

    def setUp(self):
        self.client = APIClient()

        # Создаем активного пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_active_employee=True
        )

        self.client.force_authenticate(user=self.user)

        # Создаем тестовые продукты
        self.product1 = Product.objects.create(
            name='Смартфон',
            model='X-Phone Pro',
            release_date=date.today() - timedelta(days=30)
        )

        # Создаем завод
        self.factory = NetworkNode.objects.create(
            name='Электротехнический завод "Восток"',
            node_type=NetworkNode.NodeType.FACTORY,
            email='factory@example.com',
            country='Россия',
            city='Новосибирск',
            street='Промышленная',
            house_number='15А'
        )

        # Создаем розничную сеть
        self.retail = NetworkNode.objects.create(
            name='Сеть магазинов "Электросила"',
            node_type=NetworkNode.NodeType.RETAIL,
            email='retail@example.com',
            country='Россия',
            city='Новосибирск',
            street='Ленина',
            house_number='100',
            supplier=self.factory,
            debt_to_supplier=50000.00
        )

        # Добавляем продукт к розничной сети
        self.retail.products.add(self.product1)

        self.node_list_url = reverse('network-node-list')
        self.node_detail_url = reverse('network-node-detail', args=[self.retail.id])

    def test_get_network_nodes_list(self):
        """Тест получения списка звеньев."""
        response = self.client.get(self.node_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results'] if 'results' in response.data else response.data), 2)

    def test_create_network_node(self):
        """Тест создания звена сети."""
        data = {
            'name': 'ИП Иванов',
            'node_type': NetworkNode.NodeType.INDIVIDUAL,
            'email': 'ip@example.com',
            'country': 'Россия',
            'city': 'Москва',
            'street': 'Арбат',
            'house_number': '15',
            'supplier': self.retail.id,
            'debt_to_supplier': 15000.00,
            'product_ids': [self.product1.id]
        }

        response = self.client.post(self.node_list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'ИП Иванов')
        self.assertEqual(response.data['node_type'], NetworkNode.NodeType.INDIVIDUAL)
        self.assertEqual(NetworkNode.objects.count(), 3)

    def test_get_network_node_detail(self):
        """Тест получения деталей звена."""
        response = self.client.get(self.node_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Сеть магазинов "Электросила"')
        self.assertEqual(response.data['debt_to_supplier'], '50000.00')
        self.assertEqual(len(response.data['products']), 1)

    def test_update_network_node(self):
        """Тест обновления звена."""
        data = {
            'name': 'Обновленная сеть магазинов',
            'city': 'Москва'
        }

        response = self.client.patch(self.node_detail_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Обновленная сеть магазинов')
        self.assertEqual(response.data['city'], 'Москва')

        # Проверяем, что задолженность нельзя обновить
        self.assertEqual(response.data['debt_to_supplier'], '50000.00')

    def test_cannot_update_debt_via_api(self):
        """Тест: нельзя обновить задолженность через API."""
        data = {
            'debt_to_supplier': 0  # Пытаемся обнулить долг
        }

        response = self.client.patch(self.node_detail_url, data, format='json')

        # Должен проигнорировать поле debt_to_supplier
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что долг не изменился
        self.retail.refresh_from_db()
        self.assertEqual(self.retail.debt_to_supplier, 50000.00)

    def test_clear_debt_action(self):
        """Тест action для очистки задолженности."""
        clear_debt_url = reverse('network-node-clear-debt', args=[self.retail.id])

        response = self.client.post(clear_debt_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что долг обнулился
        self.retail.refresh_from_db()
        self.assertEqual(self.retail.debt_to_supplier, 0)

    def test_filter_by_country(self):
        """Тест фильтрации по стране."""
        response = self.client.get(self.node_list_url, {'country': 'Россия'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(results), 2)  # Оба звена в России

    def test_filter_by_city(self):
        """Тест фильтрации по городу."""
        response = self.client.get(self.node_list_url, {'city': 'Новосибирск'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(results), 2)  # Оба звена в Новосибирске

    def test_statistics_endpoint(self):
        """Тест endpoint статистики."""
        statistics_url = reverse('network-node-statistics')

        response = self.client.get(statistics_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_nodes', response.data)
        self.assertIn('factories', response.data)
        self.assertIn('retail_networks', response.data)
        self.assertIn('individual_entrepreneurs', response.data)
        self.assertIn('total_debt', response.data)


class PermissionTests(APITestCase):
    """Тесты для проверки прав доступа."""

    def setUp(self):
        self.client = APIClient()

        # Создаем разных пользователей
        self.active_user = User.objects.create_user(
            email='active@example.com',
            password='testpass123',
            is_active_employee=True
        )

        self.inactive_user = User.objects.create_user(
            email='inactive@example.com',
            password='testpass123',
            is_active_employee=False
        )

        # Создаем продукт
        self.product = Product.objects.create(
            name='Тестовый продукт',
            model='Test Model',
            release_date=date.today()
        )

        self.product_list_url = reverse('product-list')

    def test_active_employee_can_access_api(self):
        """Тест: активный сотрудник может получить доступ к API."""
        self.client.force_authenticate(user=self.active_user)

        response = self.client.get(self.product_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_inactive_employee_cannot_access_api(self):
        """Тест: неактивный сотрудник не может получить доступ к API."""
        self.client.force_authenticate(user=self.inactive_user)

        response = self.client.get(self.product_list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_access_api(self):
        """Тест: неаутентифицированный пользователь не может получить доступ к API."""
        response = self.client.get(self.product_list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)