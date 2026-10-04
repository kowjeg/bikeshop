from django.contrib import admin
from django.db.models import Count, Sum

from .models import Order, OrderItem

# Register your models here.

class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    date_hierarchy = 'created_at'
    search_fields = ('id', 'user__username')
    inlines = (OrderItemInline,)
    actions = ['mark_shipped', 'show_revenue']

    @admin.action(description='Отметить как отправленные')
    def mark_shipped(self, request, queryset):
        updated = queryset.update(status=Order.Status.SHIPPED)
        self.message_user(request, f'Обновлено заказов {updated}')

    @admin.action(description='Показать выручку по выбранному')
    def show_revenue(self, request, queryset):
        agg = queryset.aggregate(total=Sum('total_price'), count=Count('id'))
        self.message_user(request,
                          f'Заказов {agg["count"]}, выручка {agg["total"]} or 0'
                          )
