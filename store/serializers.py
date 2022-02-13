from decimal import Decimal

from rest_framework import serializers

from store.models import Product, Collection


# class CollectionSerializer(serializers.Serializer):
#     id = serializers.IntegerField()
#     title = serializers.CharField(max_length=255)


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'title']


# class ProductSerializer(serializers.Serializer):
#     id = serializers.IntegerField()
#     title = serializers.CharField(max_length=255)
#     price = serializers.DecimalField(
#         max_digits=6, decimal_places=2, source='unit_price')
#     price_with_tax = serializers.SerializerMethodField(
#         method_name='calculate_price')
#     collection = CollectionSerializer()
#     collection_id = serializers.PrimaryKeyRelatedField(
#         queryset=Collection.objects.all())
#     collection_title = serializers.StringRelatedField(source='collection')
#     collection_link = serializers.HyperlinkedRelatedField(
#         queryset = Collection.objects.all(),
#         view_name='collection-detail',
#         source='collection'
#     )

#     def calculate_price(self, product: Product):
#         return product.unit_price * Decimal(1.1)


"""
{
   "title": "a",
   "slug": "a",
   "unit_price": 1,
   "inventory": 1,
   "collection": 6
}
"""
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'slug', 'inventory',
                  'unit_price', 'price_with_tax', 'collection']
        # fields = '__all__'

    price_with_tax = serializers.SerializerMethodField(
        method_name='calculate_price')

    def calculate_price(self, product: Product):
        return product.unit_price * Decimal(1.1)

    # def validate(self, data):
    #     if data['password'] != data['confirm_password']:
    #         return serializers.ValidationError('Passwords do not match')
    #     return data

    # def create(self, validated_data):
    #     product = Product(**validated_data)
    #     product.other = 1
    #     product.save()
    #     return product

    # def update(self, instance, validated_data):
    #     instance.unit_price = validated_data.get('unit_price')
    #     instance.save()
    #     return instance
    