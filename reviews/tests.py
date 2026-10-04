import pytest
from django.db import IntegrityError

from reviews.models import Review

pytestmark = pytest.mark.django_db


class TestReviewModel:
    def test_create(self, user, product):
        review = Review.objects.create(product=product, user=user, rating=5)
        assert product.reviews.count() == 1
        assert review.rating == 5

    def test_one_review_per_user(self, user, product):
        Review.objects.create(product=product, user=user, rating=5)
        with pytest.raises(IntegrityError):
            Review.objects.create(product=product, user=user, rating=4)
