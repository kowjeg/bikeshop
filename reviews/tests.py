import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.urls import reverse

from orders.models import Order, OrderItem
from reviews.models import Review
from reviews.forms import ReviewForm
from reviews.services import can_review, has_purchased


pytestmark = pytest.mark.django_db


def make_order(user, product, status=Order.Status.PAID):
    """Создаёт заказ пользователя с одной штукой товара."""
    order = Order.objects.create(user=user, status=status, total_price=product.price)
    OrderItem.objects.create(order=order, product=product, quantity=1, price=product.price)
    return order


@pytest.fixture
def purchase(user, product):
    """user купил product."""
    return make_order(user, product)


def post_review(client, product, data):
    return client.post(reverse('reviews:create', args=[product.slug]), data)


class TestReviewModel:
    def test_create(self, user, product):
        review = Review.objects.create(product=product, user=user, rating=5)
        assert product.reviews.count() == 1
        assert review.rating == 5

    def test_one_review_per_user(self, user, product):
        Review.objects.create(product=product, user=user, rating=5)
        with pytest.raises(IntegrityError):
            Review.objects.create(product=product, user=user, rating=4)


class TestHasPurchased:
    def test_anonymous(self, product):
        assert has_purchased(AnonymousUser(), product) is False

    def test_not_bought(self, user, product):
        assert has_purchased(user, product) is False

    def test_bought(self, user, product, purchase):
        assert has_purchased(user, product) is True

    def test_cancelled_order_not_counted(self, user, product):
        make_order(user, product, status=Order.Status.CANCELLED)
        assert has_purchased(user, product) is False

    def test_other_users_order_not_counted(self, user, other_user, product):
        make_order(other_user, product)
        assert has_purchased(user, product) is False


class TestCanReview:
    def test_bought_and_no_review(self, user, product, purchase):
        assert can_review(user, product) is True

    def test_already_reviewed(self, user, product, purchase):
        Review.objects.create(product=product, user=user, rating=5)
        assert can_review(user, product) is False

class TestReviewCreateView:
    def test_requires_login(self, client, product):
        response = post_review(client, product, {'rating': 5})

        assert response.status_code == 302
        assert reverse('users:login') in response.url
        assert not Review.objects.exists()

    def test_only_post(self, logged_client, product, purchase):
        response = logged_client.get(reverse('reviews:create', args=[product.slug]))
        assert response.status_code == 405

    def test_not_bought_cannot_post(self, logged_client, product):
        response = post_review(logged_client, product, {'rating': 5})

        assert response.status_code == 302
        assert response.url == reverse('products:detail', args=[product.slug])
        assert not Review.objects.exists()

    def test_creates_review(self, logged_client, user, product, purchase):
        response = post_review(logged_client, product, {'rating': 4, 'comments': 'Хороший'})

        assert response.status_code == 302
        review = Review.objects.get()
        assert review.user == user
        assert review.product == product
        assert review.rating == 4
        assert review.comments == 'Хороший'

    def test_second_review_rejected(self, logged_client, user, product, purchase):
        Review.objects.create(product=product, user=user, rating=5)

        response = post_review(logged_client, product, {'rating': 1})

        assert response.status_code == 302
        assert Review.objects.count() == 1
        assert Review.objects.get().rating == 5

    @pytest.mark.parametrize('bad', [0, 6, 'abc'])
    def test_bad_rating(self, logged_client, product, purchase, bad):
        response = post_review(logged_client, product, {'rating': bad})

        assert response.status_code == 302
        assert not Review.objects.exists()

    def test_cannot_fake_user(self, logged_client, user, other_user, product, purchase):
        post_review(logged_client, product, {'rating': 5, 'user': other_user.id})

        assert Review.objects.get().user == user


class TestProductPageReviewForm:
    def test_anonymous_sees_no_form(self, client, product):
        response = client.get(reverse('products:detail', args=[product.slug]))

        assert response.context['can_review'] is False
        assert response.context['review_form'] is None

    def test_buyer_sees_form(self, logged_client, product, purchase):
        response = logged_client.get(reverse('products:detail', args=[product.slug]))

        assert response.context['can_review'] is True
        assert isinstance(response.context['review_form'], ReviewForm)