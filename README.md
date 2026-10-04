# BikeShop

Интернет-магазин велосипедов, запчастей и аксессуаров на Django + Django REST Framework.

- **Сайт** — каталог с поиском и фильтрами, карточка товара, корзина в сессии, оформление заказа
  с письмом-подтверждением, личный кабинет. Аутентификация — сессии Django.
- **REST API** — товары, категории, заказы, регистрация. Аутентификация — JWT.
  Документация — Swagger / OpenAPI.
- **Админка** — управление товарами и заказами, фильтры, аналитика (выручка, число заказов, рейтинг).

**Стек:** Python 3.13, Django 6.1, DRF, SimpleJWT, drf-spectacular, django-filter,
PostgreSQL 16, Docker Compose, Poetry, pytest-django, ruff, mypy (django-stubs).

---

## Быстрый старт (Docker)

Нужен только Docker с Docker Compose.

```bash
git clone <url-репозитория> bikeshop
cd bikeshop

cp .env.example .env            # Windows: copy .env.example .env

docker compose up -d --build    # сборка, запуск Postgres и Django; миграции применяются сами
docker compose exec web python manage.py seed_demo   # демо-данные
```

Открыть http://localhost:8000.

| Что | Адрес |
|---|---|
| Сайт | http://localhost:8000/ |
| Админка | http://localhost:8000/admin/ |
| Swagger UI | http://localhost:8000/api/docs/ |
| OpenAPI-схема | http://localhost:8000/api/schema/ |

### Демо-данные

`seed_demo` заполняет базу за один запуск:

- 21 категория (дерево: «Велосипеды → Шоссейные / MTB / …», «Запчасти», «Аксессуары»);
- 35 товаров с картинками (исходники — `products/seed_data/images/`, лицензии — `products/seed_data/CREDITS.md`);
- администратор и 6 покупателей с заполненными профилями;
- ~25 заказов за последние 4 месяца в разных статусах — чтобы в админке были видны фильтры и аналитика;
- ~20 отзывов на купленные и доставленные товары.

| Роль | Логин | Пароль |
|---|---|---|
| Администратор | `admin` | `admin12345` |
| Покупатели | `ivan`, `maria`, `alexey`, `olga`, `dmitry`, `anna` | `BikeShop2026` |

Команда идемпотентна: повторный запуск обновит товары и не создаст дублей.
Данные детерминированы (одинаковые при каждом запуске).

```bash
docker compose exec web python manage.py seed_demo --reset   # пересоздать заказы и отзывы демо-покупателей
docker compose exec web python manage.py seed_products       # только категории и товары
```

### Письма

В dev-режиме письма не отправляются, а печатаются в лог контейнера:

```bash
docker compose logs -f web
```

### Остановка и сброс

```bash
docker compose down        # остановить
docker compose down -v     # остановить и удалить базу (volume pg_data)
```

---

## REST API и JWT

Все эндпоинты — под `/api/`. Полное описание с возможностью отправлять запросы — в Swagger: `/api/docs/`.

| Метод | URL | Доступ | Описание |
|---|---|---|---|
| POST | `/api/users/register/` | все | регистрация |
| POST | `/api/users/login/` | все | получить пару токенов `access` + `refresh` |
| POST | `/api/token/refresh/` | все | обновить `access` по `refresh` |
| GET | `/api/products/` | все | список товаров (пагинация по 12) |
| GET | `/api/products/{slug}/` | все | товар |
| GET | `/api/categories/` | все | категории |
| GET | `/api/orders/` | JWT | заказы текущего пользователя |
| GET | `/api/orders/{id}/` | JWT | заказ (только свой) |
| POST | `/api/orders/` | JWT | создать заказ |

Параметры списка товаров: `?search=garmin`, `?ordering=price` / `-price` / `avg_rating`,
`?category__name=Шины`, `?page=2`.

### Схема авторизации

1. `POST /api/users/login/` с логином и паролем → `access` (живёт 30 минут) и `refresh` (7 дней).
2. Каждый запрос к защищённому эндпоинту — с заголовком `Authorization: Bearer <access>`.
3. Когда `access` истёк (ответ `401`), `POST /api/token/refresh/` с `refresh` → новый `access`.

Оба токена — JWT (`header.payload.signature`), в payload лежат `user_id`, тип токена и срок действия `exp`.

### Примеры

```bash
# регистрация
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "rider", "email": "rider@example.com", "password": "StrongPass123"}'

# получить токены
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "ivan", "password": "BikeShop2026"}'
# → {"refresh": "eyJ...", "access": "eyJ..."}

# товары: поиск и сортировка
curl "http://localhost:8000/api/products/?search=shimano&ordering=-price"

# создать заказ
curl -X POST http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"shipping_address": "Moscow, Tverskaya 12", "items": [{"product_id": 1, "quantity": 2}]}'

# мои заказы
curl http://localhost:8000/api/orders/ -H "Authorization: Bearer <access>"

# обновить access
curl -X POST http://localhost:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh>"}'
```

Бизнес-правила заказа: нельзя заказать больше, чем есть на складе (ответ `400`, заказ не создаётся,
остатки не меняются); остатки списываются в транзакции с блокировкой строк (`select_for_update`),
поэтому два одновременных заказа не уведут склад в минус.

---

## Тесты и линтеры

Инструменты стоят в контейнере (dev-группа Poetry, образ собирается с `DEV=true`).

```bash
docker compose exec web pytest              # тесты
docker compose exec web pytest -v orders    # одно приложение, подробно
docker compose exec web ruff check .        # линтер
docker compose exec web ruff format .       # форматирование
docker compose exec web mypy .              # проверка типов
```

После изменения моделей один раз запустите `pytest --create-db` — по умолчанию тестовая база переиспользуется.

Тесты покрывают каталог и поиск, страницу товара, корзину, оформление заказа (списание остатков, письмо),
регистрацию и вход, REST API (JWT, права, чужие заказы, нехватка остатка) и ограничения моделей.

### Запуск без Docker (с хоста)

Postgres всё равно нужен — его можно оставить в контейнере (порт 5432 проброшен):

```bash
poetry install --with dev
docker compose up -d db
```

```powershell
$env:POSTGRES_HOST = "localhost"   # bash: export POSTGRES_HOST=localhost
pytest
mypy .
```

Настройки ruff, mypy и pytest — в `pyproject.toml`.

---

## Структура проекта

```
bikeshop/
├── config/                 # проект Django
│   ├── settings/           # base.py, development.py, prod.py
│   ├── urls.py             # маршруты сайта
│   └── api_urls.py         # маршруты API, JWT, Swagger
├── products/               # каталог: модели, представления, API
│   ├── management/commands/
│   │   ├── seed_products.py   # категории и товары
│   │   └── seed_demo.py       # полное демо-наполнение
│   └── seed_data/          # картинки для демо-товаров
├── orders/                 # корзина (сессия), оформление, заказы, API заказов
├── users/                  # регистрация, вход, профиль, API регистрации
├── reviews/                # отзывы
├── payments/               # оплата (заготовка)
├── templates/              # HTML-шаблоны
├── static/                 # CSS, JS, картинки вёрстки
├── conftest.py             # общие фикстуры pytest
├── Dockerfile
├── docker-compose.yaml
├── pyproject.toml          # зависимости (Poetry) и настройки инструментов
└── .env.example            # пример переменных окружения
```

---

## Чек-лист реализации

- [x] Проект запускается через Docker Compose на чистой копии.
- [x] PostgreSQL используется.
- [x] Каталог: фильтры, поиск, пагинация.
- [ ] Страница товара: детали, отзывы, добавление в корзину — *отзывы отображаются, форма добавления отзыва в разработке.*
- [x] Корзина: управление, расчёт, проверка остатков.
- [x] Оформление заказа: создание, email, валидация.
- [x] Личный кабинет: регистрация, вход, история, редактирование.
- [x] REST API: JWT, документация, права.
- [x] Админка: аналитика, фильтры, управление.
- [x] Swagger/OpenAPI работает.
- [ ] Типизация и докстринги — *частично.*
- [ ] Линтеры (ruff/mypy) без критичных ошибок — *настроены, остались мелкие замечания.*
- [x] Базовые тесты проходят.
- [x] README полон и понятен.
- [ ] Коммиты осмысленные, ветки используются.
- [x] Чек-лист приложен.
