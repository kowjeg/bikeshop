from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from products.models import Product

from .forms import ReviewForm
from .services import can_review


@login_required
@require_POST
def review_create(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)

    if not can_review(request.user, product):
        messages.error(request, 'Отзыв можно оставить только на купленный товар и только один раз.')
        return redirect('products:detail', slug=slug)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        review.save()
        messages.success(request, 'Спасибо за отзыв!')
    else:
        messages.error(request, 'Оценка должна быть от 1 до 5.')

    return redirect('products:detail', slug=slug)