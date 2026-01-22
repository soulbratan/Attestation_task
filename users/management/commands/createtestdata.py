from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from electronics_network.models import NetworkNode, Product
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    """
    Команда для создания тестовых данных: пользователей, продуктов и звеньев сети.
    """

    def handle(self, *args, **options):
        User = get_user_model()

        self.stdout.write(self.style.NOTICE("Создание тестовых данных..."))

        # Создаем суперпользователя если нет
        self.create_superuser()

        # Создаем 5 обычных пользователей
        self.create_test_users()

        # Создаем продукты
        self.create_products()

        # Создаем сеть
        self.create_network()

        self.stdout.write(self.style.SUCCESS("Тестовые данные успешно созданы!"))

    def create_superuser(self):
        """Создает суперпользователя если его нет."""
        User = get_user_model()

        if not User.objects.filter(email="admin@electronics.com").exists():
            User.objects.create_superuser(
                email="admin@electronics.com",
                password="admin123",
                first_name="Алексей",
                last_name="Петров",
                is_active_employee=True
            )
            self.stdout.write(
                self.style.SUCCESS("✓ Создан суперпользователь: admin@electronics.com (пароль: admin123)"))

    def create_test_users(self):
        """Создает 5 тестовых пользователей."""
        User = get_user_model()

        test_users = [
            {
                "email": "manager1@electronics.com",
                "password": "manager123",
                "first_name": "Иван",
                "last_name": "Сидоров",
                "is_active_employee": True,
                "is_staff": True
            },
            {
                "email": "manager2@electronics.com",
                "password": "manager123",
                "first_name": "Мария",
                "last_name": "Иванова",
                "is_active_employee": True,
                "is_staff": True
            },
            {
                "email": "employee1@electronics.com",
                "password": "employee123",
                "first_name": "Андрей",
                "last_name": "Кузнецов",
                "is_active_employee": True,
                "is_staff": False
            },
            {
                "email": "employee2@electronics.com",
                "password": "employee123",
                "first_name": "Ольга",
                "last_name": "Смирнова",
                "is_active_employee": True,
                "is_staff": False
            },
            {
                "email": "inactive@electronics.com",
                "password": "inactive123",
                "first_name": "Дмитрий",
                "last_name": "Васильев",
                "is_active_employee": False,  # Не активный сотрудник
                "is_staff": False
            }
        ]

        created_count = 0
        for user_data in test_users:
            if not User.objects.filter(email=user_data["email"]).exists():
                is_staff = user_data.pop("is_staff", False)

                user = User.objects.create_user(**user_data)
                user.is_staff = is_staff
                user.save()

                created_count += 1
                status = "активный сотрудник" if user_data["is_active_employee"] else "неактивный"
                self.stdout.write(
                    f"Создан пользователь: {user.email} ({user.first_name} {user.last_name}) - {status}")

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f"Создано {created_count} тестовых пользователей"))

    def create_products(self):
        """Создает тестовые продукты."""
        products_data = [
            {
                "name": "Смартфон",
                "model": "X-Phone Pro",
                "release_date": timezone.now().date() - timedelta(days=30)
            },
            {
                "name": "Ноутбук",
                "model": "UltraBook Z",
                "release_date": timezone.now().date() - timedelta(days=60)
            },
            {
                "name": "Планшет",
                "model": "TabMaster 10",
                "release_date": timezone.now().date() - timedelta(days=90)
            },
            {
                "name": "Умные часы",
                "model": "SmartWatch 3",
                "release_date": timezone.now().date() - timedelta(days=120)
            },
            {
                "name": "Наушники",
                "model": "SoundBlast Pro",
                "release_date": timezone.now().date() - timedelta(days=150)
            },
            {
                "name": "Телевизор",
                "model": "QLED 4K",
                "release_date": timezone.now().date() - timedelta(days=180)
            },
            {
                "name": "Игровая консоль",
                "model": "GameBox X",
                "release_date": timezone.now().date() - timedelta(days=210)
            },
            {
                "name": "Фотоаппарат",
                "model": "PhotoShot Pro",
                "release_date": timezone.now().date() - timedelta(days=240)
            }
        ]

        created_count = 0
        for product_data in products_data:
            if not Product.objects.filter(name=product_data["name"], model=product_data["model"]).exists():
                Product.objects.create(**product_data)
                created_count += 1

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✓ Создано {created_count} тестовых продуктов"))

    def create_network(self):
        """Создает тестовую сеть звеньев."""
        # Получаем все продукты
        all_products = list(Product.objects.all())

        # Создаем заводы
        factories = []
        factory_data = [
            {
                "name": "Электротехнический завод 'Восток'",
                "node_type": NetworkNode.NodeType.FACTORY,
                "email": "factory1@electronics.com",
                "country": "Россия",
                "city": "Новосибирск",
                "street": "Промышленная",
                "house_number": "15А",
                "debt_to_supplier": 0
            },
            {
                "name": "Завод 'ТехноПром'",
                "node_type": NetworkNode.NodeType.FACTORY,
                "email": "factory2@electronics.com",
                "country": "Россия",
                "city": "Москва",
                "street": "Заводская",
                "house_number": "42",
                "debt_to_supplier": 0
            }
        ]

        for data in factory_data:
            if not NetworkNode.objects.filter(email=data["email"]).exists():
                factory = NetworkNode.objects.create(**data)
                # Добавляем случайные продукты
                if all_products:
                    factory.products.set(random.sample(all_products, min(4, len(all_products))))
                factories.append(factory)
                self.stdout.write(f"✓ Создан завод: {factory.name} в {factory.city}")

        if not factories:
            return

        # Создаем розничные сети
        retail_networks = []
        retail_data = [
            {
                "name": "Сеть магазинов 'Электросила'",
                "node_type": NetworkNode.NodeType.RETAIL,
                "email": "retail1@electronics.com",
                "country": "Россия",
                "city": "Новосибирск",
                "street": "Ленина",
                "house_number": "100",
                "supplier": factories[0],
                "debt_to_supplier": random.choice([0, 50000, 75000, 100000])
            },
            {
                "name": "Торговый дом 'Техномир'",
                "node_type": NetworkNode.NodeType.RETAIL,
                "email": "retail2@electronics.com",
                "country": "Россия",
                "city": "Москва",
                "street": "Тверская",
                "house_number": "25",
                "supplier": factories[1],
                "debt_to_supplier": random.choice([0, 30000, 60000, 90000])
            },
            {
                "name": "Сеть 'ГаджетЛенд'",
                "node_type": NetworkNode.NodeType.RETAIL,
                "email": "retail3@electronics.com",
                "country": "Россия",
                "city": "Санкт-Петербург",
                "street": "Невский проспект",
                "house_number": "50",
                "supplier": factories[0],
                "debt_to_supplier": random.choice([0, 40000, 80000])
            }
        ]

        for data in retail_data:
            if not NetworkNode.objects.filter(email=data["email"]).exists():
                retail = NetworkNode.objects.create(**data)
                if all_products:
                    retail.products.set(random.sample(all_products, min(3, len(all_products))))
                retail_networks.append(retail)
                self.stdout.write(
                    f"Создана розничная сеть: {retail.name} в {retail.city} (долг: {retail.debt_to_supplier} руб.)")

        # Создаем индивидуальных предпринимателей
        ip_data = [
            {
                "name": "ИП Иванов А.С.",
                "node_type": NetworkNode.NodeType.INDIVIDUAL,
                "email": "ip1@electronics.com",
                "country": "Россия",
                "city": "Новосибирск",
                "street": "Кирова",
                "house_number": "10",
                "supplier": retail_networks[0] if retail_networks else None,
                "debt_to_supplier": random.choice([0, 15000, 25000, 35000])
            },
            {
                "name": "ИП Петрова М.И.",
                "node_type": NetworkNode.NodeType.INDIVIDUAL,
                "email": "ip2@electronics.com",
                "country": "Россия",
                "city": "Москва",
                "street": "Арбат",
                "house_number": "15",
                "supplier": retail_networks[1] if len(retail_networks) > 1 else None,
                "debt_to_supplier": random.choice([0, 12000, 18000, 22000])
            },
            {
                "name": "ИП Сидоров В.П.",
                "node_type": NetworkNode.NodeType.INDIVIDUAL,
                "email": "ip3@electronics.com",
                "country": "Россия",
                "city": "Екатеринбург",
                "street": "Малышева",
                "house_number": "30",
                "supplier": retail_networks[0] if retail_networks else None,
                "debt_to_supplier": random.choice([0, 8000, 12000, 16000])
            },
            {
                "name": "ИП Козлова Е.В.",
                "node_type": NetworkNode.NodeType.INDIVIDUAL,
                "email": "ip4@electronics.com",
                "country": "Россия",
                "city": "Казань",
                "street": "Баумана",
                "house_number": "20",
                "supplier": retail_networks[2] if len(retail_networks) > 2 else None,
                "debt_to_supplier": random.choice([0, 10000, 15000, 20000])
            }
        ]

        ip_count = 0
        for data in ip_data:
            if not NetworkNode.objects.filter(email=data["email"]).exists():
                ip = NetworkNode.objects.create(**data)
                if all_products:
                    ip.products.set(random.sample(all_products, min(2, len(all_products))))
                ip_count += 1
                self.stdout.write(f"✓ Создан ИП: {ip.name} в {ip.city} (долг: {ip.debt_to_supplier} руб.)")

        self.stdout.write(self.style.SUCCESS(
            f"Создана тестовая сеть: 2 завода, {len(retail_networks)} розничных сетей, {ip_count} ИП"))
