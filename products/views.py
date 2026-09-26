from decimal import Decimal, InvalidOperation

from django.db.models import Avg, F, Q
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Product, Category


# Create your views here.


class ProductListView(ListView):
    model = Product
    template_name = 'home.html'
    context_object_name = 'products'
    paginate_by = 10

    # ключ в ?sort= -> (подпись кнопки, сортировка)
    SORT_OPTIONS = {
        'new': ('New', '-created_at'),
        'price_asc': ('Price ascending', 'price'),
        'price_desc': ('Price descending', '-price'),
        'rating': ('Rating', F('avg_rating').desc(nulls_last=True)),
    }
    DEFAULT_SORT = 'new'

    def get_sort(self):
        sort = self.request.GET.get('sort', self.DEFAULT_SORT)
        return sort if sort in self.SORT_OPTIONS else self.DEFAULT_SORT

    def get_price(self, name):
        """Цена из ?min_price= / ?max_price=; мусор вроде 'abc' или -5 игнорируем."""
        try:
            price = Decimal(self.request.GET.get(name, ''))
        except InvalidOperation:
            return None
        return price if price.is_finite() and price >= 0 else None

    def get_queryset(self):
        qs = (
            Product.objects.filter(is_active=True)
            .select_related('category')
            .annotate(avg_rating=Avg('reviews__rating'))
        )

        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))

        categories = self.request.GET.getlist('categories')
        if categories:
            # выбрали «Велосипеды» — показываем и товары из подкатегорий (Шоссейные, MTB, ...)
            qs = qs.filter(Q(category__slug__in=categories) | Q(category__parent__slug__in=categories))

        min_price = self.get_price('min_price')
        max_price = self.get_price('max_price')

        if min_price is not None:
            qs = qs.filter(price__gte=min_price)

        if max_price is not None:
            qs = qs.filter(price__lte=max_price)

        _, ordering = self.SORT_OPTIONS[self.get_sort()]
        # pk — чтобы порядок был стабильным при одинаковых ценах/датах и товары не "прыгали" между страницами
        return qs.order_by(ordering, 'pk')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # корневые категории, у каждой .children — подкатегории (для дерева в сайдбаре)
        context['categories'] = Category.objects.filter(parent=None).prefetch_related('children')
        context['query'] = self.request.GET.get('q', '')
        context['min_price'] = self.get_price('min_price')
        context['max_price'] = self.get_price('max_price')
        selected = self.request.GET.getlist('categories')
        context['selected_categories'] = selected
        context['current_sort'] = self.get_sort()
        context['sort_options'] = [(key, label) for key, (label, _) in self.SORT_OPTIONS.items()]

        params = self.request.GET.copy()
        params.pop('page', None)
        context['querystring'] = params.urlencode()

        # теги выбранных категорий: (название, ссылка на ту же выдачу без этой категории)
        tags = []
        for category in Category.objects.filter(slug__in=selected):
            without = params.copy()
            without.setlist('categories', [slug for slug in selected if slug != category.slug])
            tags.append((category.name, without.urlencode()))
        context['category_tags'] = tags

        # для кнопок сортировки: все текущие фильтры, кроме sort и page
        params.pop('sort', None)
        context['sort_querystring'] = params.urlencode()
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'product-detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related('category')
            .annotate(avg_rating=Avg('reviews__rating'))
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['review_form'] = None #TODO ReviewForm()

        user = self.request.user
        ctx['can_review'] = (
            user.is_authenticated
            #TODO логика прошлой покупки пользователем
        )

        return ctx