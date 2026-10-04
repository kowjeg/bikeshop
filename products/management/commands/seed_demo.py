import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from orders.models import Order, OrderItem
from products.models import Product
from reviews.models import Review
from users.models import Profile

User = get_user_model()

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin12345'
DEMO_PASSWORD = 'BikeShop2026'

# (username, email, full_name, phone, city, address)
DEMO_USERS = [
    ('ivan', 'ivan@bikeshop.local', 'Иван Петров', '+7 900 111-22-33', 'Москва', 'ул. Тверская, 12, кв. 5'),
    ('maria', 'maria@bikeshop.local', 'Мария Смирнова', '+7 900 222-33-44', 'Санкт-Петербург', 'Невский пр., 48, кв. 17'),
    ('alexey', 'alexey@bikeshop.local', 'Алексей Кузнецов', '+7 900 333-44-55', 'Казань', 'ул. Баумана, 7'),
    ('olga', 'olga@bikeshop.local', 'Ольга Соколова', '+7 900 444-55-66', 'Екатеринбург', 'ул. Ленина, 25, кв. 3'),
    ('dmitry', 'dmitry@bikeshop.local', 'Дмитрий Волков', '+7 900 555-66-77', 'Новосибирск', 'Красный пр., 101'),
    ('anna', 'anna@bikeshop.local', 'Анна Морозова', '+7 900 666-77-88', 'Сочи', 'Курортный пр., 33, кв. 9'),
]

# отзывы по оценке: чтобы текст совпадал с количеством звёзд
REVIEW_TEXTS = {
    5: [
        'Отличная вещь, рекомендую к покупке!',
        'Всё как в описании, доставили быстро. Рекомендую.',
        'Пользуюсь уже месяц — ни одного нарекания.',
        'Лучшая покупка за последнее время. Цена оправдана.',
    ],
    4: [
        'Хорошее качество, но цена могла бы быть пониже.',
        'В целом хорошо, есть мелкие недочёты в сборке.',
        'Работает отлично, упаковка была немного помята.',
    ],
    3: [
        'Нормально, но за эти деньги хотелось большего.',
        'Средне. Свою задачу выполняет, не более того.',
    ],
    2: [
        'Пришлось дорабатывать после покупки — неприятно.',
    ],
}
RATING_WEIGHTS = {5: 50, 4: 30, 3: 15, 2: 5}

# статусы, которые бывают у старых и у свежих заказов
OLD_STATUSES = [Order.Status.DELIVERED] * 6 + [Order.Status.CANCELLED]
RECENT_STATUSES = [Order.Status.PAID, Order.Status.SHIPPED, Order.Status.PENDING]

ORDERS_PER_USER = (3, 6)
DAYS_BACK = 120


class Command(BaseCommand):
    help = (
        'Первичное заполнение базы демо-данными: категории и товары с картинками, '
        'администратор, покупатели с профилями, заказы и отзывы.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Удалить заказы и отзывы демо-покупателей и сгенерировать их заново.',
        )
        parser.add_argument(
            '--seed',
            type=int,
            default=42,
            help='Зерно генератора: одинаковое зерно — одинаковые данные (по умолчанию 42).',
        )

    def handle(self, *args, **options):
        call_command('seed_products', stdout=self.stdout)

        rng = random.Random(options['seed'])
        with transaction.atomic():
            self.create_admin()
            users = self.create_users()

            demo_orders = Order.objects.filter(user__in=users)
            if options['reset']:
                Review.objects.filter(user__in=users).delete()
                demo_orders.delete()

            if demo_orders.exists():
                self.stdout.write(self.style.WARNING(
                    'Заказы демо-покупателей уже есть — пропускаю (пересоздать: --reset).'
                ))
                return

            orders = self.create_orders(users, rng)
            reviews = self.create_reviews(users, rng)

        self.stdout.write(self.style.SUCCESS(
            f'Покупателей: {len(users)}, заказов: {orders}, отзывов: {reviews}.'
        ))
        self.stdout.write(
            f'Админка: /admin/ — {ADMIN_USERNAME} / {ADMIN_PASSWORD}\n'
            f'Покупатели: {", ".join(u.username for u in users)} — пароль {DEMO_PASSWORD}'
        )

    def create_admin(self):
        if not User.objects.filter(username=ADMIN_USERNAME).exists():
            User.objects.create_superuser(ADMIN_USERNAME, 'admin@bikeshop.local', ADMIN_PASSWORD)

    def create_users(self):
        users = []
        for username, email, full_name, phone, city, address in DEMO_USERS:
            user = User.objects.filter(username=username).first()
            if user is None:
                user = User.objects.create_user(username, email, DEMO_PASSWORD)
            Profile.objects.update_or_create(
                user=user,
                defaults={'full_name': full_name, 'phone': phone, 'city': city, 'address': address},
            )
            users.append(user)
        return users

    def create_orders(self, users, rng):
        products = list(Product.objects.filter(is_active=True))
        now = timezone.now()
        count = 0

        for user in users:
            profile = user.profile
            address = f'{profile.full_name}, {profile.phone}\n{profile.city}, {profile.address}'

            for _ in range(rng.randint(*ORDERS_PER_USER)):
                created_at = now - timedelta(
                    days=rng.randint(0, DAYS_BACK),
                    hours=rng.randint(0, 23),
                    minutes=rng.randint(0, 59),
                )
                age = (now - created_at).days
                status = rng.choice(OLD_STATUSES if age > 14 else RECENT_STATUSES)

                order = Order.objects.create(
                    user=user, status=status, total_price=0, shipping_address=address,
                )
                total = Decimal('0')
                # обычно в заказе один велосипед или пара-тройка запчастей/аксессуаров
                for product in rng.sample(products, k=rng.choice([1, 1, 2, 3])):
                    quantity = 1 if product.price > 20000 else rng.randint(1, 3)
                    OrderItem.objects.create(
                        order=order, product=product, quantity=quantity, price=product.price,
                    )
                    total += product.price * quantity

                # created_at — auto_now_add, поэтому дату в прошлом ставим через update()
                Order.objects.filter(pk=order.pk).update(
                    total_price=total, created_at=created_at, updated_at=created_at,
                )
                count += 1
        return count

    def create_reviews(self, users, rng):
        """Отзыв оставляют только на купленные и полученные товары, примерно на 60% из них."""
        delivered = (
            OrderItem.objects
            .filter(order__user__in=users, order__status=Order.Status.DELIVERED)
            .select_related('order')
            .order_by('order__created_at')
        )
        ratings, weights = list(RATING_WEIGHTS), list(RATING_WEIGHTS.values())
        seen = set()
        count = 0

        for item in delivered:
            key = (item.product_id, item.order.user_id)
            if key in seen or rng.random() > 0.6:
                continue
            seen.add(key)

            rating = rng.choices(ratings, weights)[0]
            review = Review.objects.create(
                product_id=item.product_id,
                user_id=item.order.user_id,
                rating=rating,
                comments=rng.choice(REVIEW_TEXTS[rating]),
            )
            reviewed_at = item.order.created_at + timedelta(days=rng.randint(5, 14))
            Review.objects.filter(pk=review.pk).update(created_at=min(reviewed_at, timezone.now()))
            count += 1
        return count
