from django.shortcuts import render
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.db import transaction
from django.db.models import Q, F, Value, Func, Count, Min, Max, Avg, Sum, ExpressionWrapper
from django.db.models.functions import Concat
from store.models import Cart, CartItem, Collection, Customer, Order, OrderItem, Product
from tags.models import TaggedItem

def say_hello(request):
    # Query sets are lazy - they are executed in for-loop, in list converting and in element accessing
    # query_set = Product.objects.all()
    # query_set.filter().filter().order_by()
    # for product in query_set:
    #     print(product)

    try:
        product = Product.objects.get(pk=1)
    except ObjectDoesNotExist:
        pass

    # None in case pk=1 does not exist
    product = Product.objects.filter(pk=1).first()

    # WHERE unit_price > 20
    # See https://docs.djangoproject.com/en/4.0/ref/models/querysets/#field-lookups
    products_queryset = Product.objects.filter(unit_price__gt=20)

    # Other Field Lookups
    products_queryset = Product.objects.filter(unit_price__range=(20, 30))
    products_queryset = Product.objects.filter(collection__id__in=(1, 2, 3))
    products_queryset = Product.objects.filter(title__icontains='coffee')
    products_queryset = Product.objects.filter(last_update__year=2021)
    products_queryset = Product.objects.filter(inventory__lt=10)
    customers_queryset = Customer.objects.filter(email__endswith='.com')
    collections_queryset = Collection.objects.filter(featured_product__isnull=True)
    orders_queryset = Order.objects.filter(customer__id=1)

    # Navigation
    order_items_queryset = OrderItem.objects.filter(product__collection__id=3)

    # And
    products_queryset = Product.objects.filter(inventory__lt=10, unit_price__lt=20)
    products_queryset = Product.objects.filter(inventory__lt=10).filter(unit_price__lt=20)

    # Or
    products_queryset = Product.objects.filter(Q(inventory__lt=10) | Q(unit_price__lt=20))

    # Not
    products_queryset = Product.objects.filter(~Q(inventory=10))

    # Referencing Fields
    products_queryset = Product.objects.filter(inventory=F('unit_price'))
    products_queryset = Product.objects.filter(inventory=F('collection__id'))

    # Sorting
    products_queryset = Product.objects.order_by('title')
    products_queryset = Product.objects.order_by('unit_price', 'title')

    # Descending Order
    products_queryset = Product.objects.order_by('title').reverse()
    products_queryset = Product.objects.order_by('-title')

    # Order and Pick One
    product = Product.objects.order_by('unit_price')[0]
    product = Product.objects.earliest('unit_price')
    product = Product.objects.latest('unit_price')

    # Limit and Offset
    products_queryset = Product.objects.all()[:5]
    products_queryset = Product.objects.all()[5:10]

    # Selecting Fields
    products_dic = Product.objects.values('title', 'unit_price', 'collection__title')
    products_tuple = Product.objects.values_list('title', 'unit_price', 'collection__title')
    
    # Exercise
    products_queryset = Product.objects.filter(
        id__in=OrderItem.objects.values('product__id').distinct()).order_by('title')

    # Deferring - other fields will be queried later, when you access them
    products_queryset = Product.objects.only('id', 'title')
    products_queryset = Product.objects.defer('description')

    # Loading Related Objects
    products_queryset = Product.objects.select_related('collection').all()
    # select_related (1)
    products_queryset = Product.objects.select_related('collection__someOtherFiels').all()
    # prefetch_related (n)
    products_queryset = Product.objects.prefetch_related('promotions').all()
    # Together
    products_queryset = Product.objects.prefetch_related('promotions').select_related('collection').all()

    # Exercise
    order_items = list(OrderItem.objects.all().select_related(
        'order', 'order__customer', 'product').defer('product__description').order_by('-order__placed_at')[:5])
    order_items.reverse()

    orders_queryset = Order.objects.select_related(
        'customer').prefetch_related('orderitem_set__product').order_by('-placed_at')[:5]

    # Aggregating
    result = Product.objects.aggregate(count=Count('id'), min_price=Min('unit_price'))

    # Exercise
    result = Order.objects.aggregate(count=Count('id'))
    result = OrderItem.objects \
        .filter(product__id=1, order__payment_status='C') \
        .aggregate(sum=Sum('quantity'))
    result = Order.objects \
        .filter(customer__id=1) \
        .aggregate(count=Count('id'))
    result = Product.objects \
        .filter(collection__id=3) \
        .aggregate(
            min=Min('unit_price'),
            max=Max('unit_price'),
            avg=Avg('unit_price'))

    # Annotating
    result = Customer.objects.annotate(is_new=Value(True))
    result = Customer.objects.annotate(new_id=F('id') + 1)
    result = Customer.objects.annotate(full_name=Func(F('first_name'), Value(' '), F('last_name'), function='CONCAT'))
    result = Customer.objects.annotate(full_name=Concat('first_name', Value(' '), 'last_name'))

    # Grouping
    result = Customer.objects.annotate(order_count=Count('order')) # ! not order_set

    # ExpressionWrapper
    discounted_price = ExpressionWrapper(F('unit_price') * 0.8, output_field=models.DecimalField())
    result = Product.objects.annotate(discounted_price=discounted_price)

    # Exercise
    result = Customer.objects.annotate(last_order=Max('order__id'))
    result = Collection.objects.annotate(product_count=Count('product'))
    result = Customer.objects \
        .annotate(order_count=Count('order')) \
        .filter(order_count__gt=5)
    result = Customer.objects \
        .filter(order__payment_status='C') \
        .annotate(total_spend=Sum(F('order__orderitem__unit_price') * F('order__orderitem__quantity')))
    result = Product.objects \
        .filter(orderitem__order__payment_status='C') \
        .annotate(sales_sum=Sum(
            F('orderitem__quantity') +
            F('orderitem__unit_price'))) \
        .order_by('-sales_sum')[:5]

    # Querying Generic Reletionships
    content_type = ContentType.objects.get_for_model(Product)
    result = TaggedItem.objects \
        .select_related('tag') \
        .filter(
            content_type=content_type,
            object_id=1
        )

    # Custom Manager
    result = TaggedItem.objects.get_tags_for(Product, 1)

    # Creating Object
    collection = Collection()
    # collection = Collection(title='Video Games')
    collection.title = 'Video Games'
    collection.featured_product = Product(pk=1)
    # collection.featured_product_id = 1
    # collection = collection.objects.create(title='Video Games', featured_product_id=1)

    # collection.save()
    # result = collection.id

    # Updating Object
    # ! All fields must be set
    collection2 = Collection(pk=11)
    collection2.title = 'Games'
    collection2.featured_product = None
    # collection2.save()

    collection3 = Collection.objects.get(pk=11)
    collection3.featured_product = None
    # collection3.save()

    Collection.objects.filter(pk=11).update(featured_product=None)

    # Deleting Object
    collection4 = Collection(pk=11)
    # collection4.delete()
    # collection4.objects.filter(id_gt=5).delete()

    # Exercise
    cart = Cart()
    cart.save()
    item = CartItem()
    item.product_id = 1
    item.quantity = 10
    item.cart = cart
    item.save()
    item = CartItem.objects.get(pk=item.id)
    item.quantity = 9
    item.save()
    cart = Cart.objects.get(pk=cart.id)
    cart.delete()

    # Transactions
    createOrderWithItem()

    with transaction.atomic():
        order = Order()
        order.customer_id = 1
        # order.save()

        item = OrderItem()
        item.order = order
        item.product_id = 1
        item.quantity = 1
        item.unit_price = 10
        # item.save()

    # Raw SQL Queries
    result = list(Product.objects.raw('SELECT * FROM store_product'))
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT * FROM `store_orderitem` \
            INNER JOIN `store_order` \
            ON (`store_orderitem`.`order_id` = `store_order`.`id`) \
            ORDER BY `store_order`.`placed_at` DESC LIMIT 5'
        )
        # cursor.callproc('get_customers', [1, 2, 'a'])

    return render(request, 'hello.html', {
        'name': 'Mosh',
        'result': result,
        # 'order_items': list(order_items_queryset),
        # 'orders': list(orders_queryset),
        # 'collections': list(collections_queryset),
        # 'customers': list(customers_queryset),
        # 'products': list(products_queryset),
        # 'products': products_dic,
        # 'order_items': order_items,
    })

@transaction.atomic()
def createOrderWithItem():
    order = Order()
    order.customer_id = 1
    # order.save()

    item = OrderItem()
    item.order = order
    item.product_id = 1
    item.quantity = 1
    item.unit_price = 10
    # item.save()

