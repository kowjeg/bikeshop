from django.db.models import Avg, Q
from django.shortcuts import render
from django.views.generic import ListView
from .models import Product, Category


# Create your views here.


class ProductListView(ListView):
    model = Product
    template_name = 'home.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        qs = (
            Product.objects.filter(is_active=True)
            .select_related('category')
            .annotate(avg_price=Avg('price'))
        )

        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))

        categories = self.request.GET.getlist('categories')
        if categories:
            qs = qs.filter(category__slug__in=categories)

        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if min_price:
            qs = qs.filter(price__gte=min_price)

        if max_price:
            qs = qs.filter(price__lte=max_price)

        sort_map = {
            'new' : '-created_at',
            'price_asc' : 'price',
            'price_desc' : '-price',
            'rating' : 'rating',

        }
        sort = self.request.GET.get('sort', default='new')
        return qs.order_by(sort_map[sort])


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['query'] = self.request.GET.get('q')
        context['min_price'] = self.request.GET.get('min_price')
        context['max_price'] = self.request.GET.get('max_price')
        context['selected_categories'] = self.request.GET.getlist('category')
        context['current_sort'] = self.request.GET.get('sort', default='new')

        params = self.request.GET.copy()
        params.pop('page', None)

        context['querystring'] = self.request.GET.urlencode()
        return context

