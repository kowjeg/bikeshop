from django.contrib import admin
from django.db.models import Avg, Count

from .models import Product, Category


# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name','slug', 'parent')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','price','category', 'stock', 'is_active', 'orders_count', 'avg_rating')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('stock', 'price', 'is_active')
    actions = ['activate', 'deactivate']


    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _orders_count=Count('order_items__order', distinct=True),
            _avg_rating=Avg('reviews__rating'),
        )

    @admin.display(description='Заказов', ordering='_orders_count')
    def orders_count(self, obj):
        return obj._orders_count

    @admin.display(description='Рейтинг', ordering='_avg_rating')
    def avg_rating(self, obj):
        return round(obj._avg_rating, 1) if obj._avg_rating is not None else '—'

    @admin.action(description='Активировать выбранные')
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано: {updated}')

    @admin.action(description='Деактивировать выбранные')
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано: {updated}')



