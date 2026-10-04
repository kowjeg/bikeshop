import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from conftest import PASSWORD
from orders.models import Order

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------- сайт ----------

class TestRegisterView:
    url = reverse('users:register')

    def test_page_opens(self, client):
        assert client.get(self.url).status_code == 200

    def test_register(self, client):
        response = client.post(self.url, {
            'username': 'NewUser',
            'email': 'new@test.ru',
            'password': PASSWORD,
        })
        assert response.status_code == 302
        user = User.objects.get(email='new@test.ru')
        assert user.username == 'newuser'  # логин приводится к нижнему регистру
        assert '_auth_user_id' in client.session  # сразу залогинен

    def test_duplicate_email(self, client, user):
        response = client.post(self.url, {
            'username': 'another',
            'email': user.email,
            'password': PASSWORD,
        })
        assert response.status_code == 200  # форма с ошибкой
        assert not User.objects.filter(username='another').exists()


class TestLoginView:
    url = reverse('users:login')

    def test_login(self, client, user):
        response = client.post(self.url, {'username': user.username, 'password': PASSWORD})
        assert response.status_code == 302
        assert '_auth_user_id' in client.session

    def test_wrong_password(self, client, user):
        response = client.post(self.url, {'username': user.username, 'password': 'wrong'})
        assert response.status_code == 200
        assert '_auth_user_id' not in client.session

    def test_logout(self, logged_client):
        logged_client.get(reverse('users:logout'))
        assert '_auth_user_id' not in logged_client.session


class TestProfileView:
    url = reverse('users:profile')

    def test_requires_login(self, client):
        response = client.get(self.url)
        assert response.status_code == 302

    def test_update(self, logged_client, user):
        response = logged_client.post(self.url, {
            'full_name': 'Иван',
            'phone': '123',
            'city': 'Москва',
            'address': 'ул. Пушкина',
            'email': 'changed@test.ru',
        })
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.email == 'changed@test.ru'
        assert user.profile.city == 'Москва'

    def test_order_history_shows_only_own_orders(self, logged_client, user, other_user):
        own = Order.objects.create(user=user, total_price=100)
        foreign = Order.objects.create(user=other_user, total_price=200)

        response = logged_client.get(self.url)
        assert list(response.context['orders_page']) == [own]
        assert f'#{own.id}' in response.content.decode()
        assert f'#{foreign.id}' not in response.content.decode()


# ---------- API ----------

class TestRegisterAPI:
    url = '/api/users/register/'

    def test_register(self, api_client):
        response = api_client.post(self.url, {
            'username': 'ApiUser',
            'email': 'api@test.ru',
            'password': PASSWORD,
        })
        assert response.status_code == 201
        assert 'password' not in response.data

        user = User.objects.get(username='apiuser')
        assert user.check_password(PASSWORD)  # пароль захеширован, а не сохранён как есть

    def test_duplicate_username(self, api_client, user):
        response = api_client.post(self.url, {
            'username': user.username.upper(),
            'email': 'x@test.ru',
            'password': PASSWORD,
        })
        assert response.status_code == 400
        assert 'username' in response.data

    def test_weak_password(self, api_client):
        response = api_client.post(self.url, {
            'username': 'weak',
            'email': 'weak@test.ru',
            'password': '123',
        })
        assert response.status_code == 400
        assert 'password' in response.data


class TestJWT:
    def test_login_returns_tokens(self, api_client, user):
        response = api_client.post('/api/users/login/', {
            'username': user.username,
            'password': PASSWORD,
        })
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_token_gives_access(self, api_client, user):
        tokens = api_client.post('/api/users/login/', {
            'username': user.username,
            'password': PASSWORD,
        }).data
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        assert api_client.get('/api/orders/').status_code == 200

    def test_wrong_password(self, api_client, user):
        response = api_client.post('/api/users/login/', {
            'username': user.username,
            'password': 'wrong',
        })
        assert response.status_code == 401
