from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, urlencode

from . import models

# Register your models here.


class InventoryFilter(admin.SimpleListFilter):
    title = 'inventory'
    parameter_name = 'inventory'

    def lookups(self, request, model_admin):
        return [
            ('<10', 'Low')
        ]

    def queryset(self, request, queryset):
        if self.value() == '<10':
            return queryset.filter(inventory__lt=10)


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'unit_price', 'inventory_status', 'collection_title']
    list_editable = ['unit_price']
    list_per_page = 10
    list_select_related = ['collection']
    # Other option: https://docs.djangoproject.com/en/4.0/ref/contrib/admin/#modeladmin-options
    list_filter = ['collection', 'last_update', InventoryFilter]
    ordering = ['title']
    search_fields = ['title']

    actions = ['clear_inventory']

    autocomplete_fields = ['collection']
    # fields = ['title', 'unit_price']
    # exclude = ['promotions']
    # readonly_fields = ['title']
    prepopulated_fields = {
        'slug': ['title']
    }

    @admin.display(ordering='inventory')
    def inventory_status(self, product):
        if (product.inventory < 10):
            return 'Low'
        return 'OK'

    def collection_title(self, product):
        return product.collection.title

    @admin.action(description='Clear inventory')
    def clear_inventory(self, request, queryset):
        updated_count = queryset.update(inventory=0)
        self.message_user(
            request,
            f'{updated_count} products were successfully updated.',
            messages.WARNING
        )


# Not needed when using decorator
# admin.site.register(models.Product, ProductAdmin)


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'products_count']
    search_fields = ['title']
    ordering = ['title']

    @admin.display(ordering='products_count')
    def products_count(self, collection):
        url = (
            # reverse('admin:app_model_page')
            reverse('admin:store_product_changelist')
            + '?'
            + urlencode({
                'collection__id': str(collection.id)
            }))
        return format_html('<a href="{}">{}</a>', url, collection.products_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(products_count=Count('product'))


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'membership', 'orders_count']
    list_editable = ['membership']
    list_per_page = 10
    search_fields = ['first_name__istartswith', 'last_name__istartswith']
    ordering = ['first_name', 'last_name']

    @admin.display(description='Orders', ordering='orders_count')
    def orders_count(self, customer):
        url = (
            reverse('admin:store_order_changelist')
            + '?'
            + urlencode({
                'customer__id': str(customer.id)
            }))
        return format_html('<a href="{}">{}</a>', url, customer.orders_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(orders_count=Count('order'))


#class OrderItemIline(admin.TabularInline):
class OrderItemIline(admin.StackedInline):
    model = models.OrderItem
    autocomplete_fields = ['product']
    extra = 0
    min_num = 1
    max_num = 10


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'placed_at', 'customer']
    list_per_page = 10
    list_select_related = ['customer']
    ordering = ['placed_at']

    autocomplete_fields = ['customer']
    inlines = [OrderItemIline]
