from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class Customer(User):
    basket_free = models.BooleanField()

class Category(models.Model):
    title = models.CharField(max_length=100)


class Product(models.Model):
    title = models.CharField(max_length=100)
    price = models.IntegerField()
    description = models.CharField(max_length=255)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, default=None, null=True)


class Basket(models.Model):
    quantity = models.IntegerField()
    basket_group_id = models.IntegerField()
    product = models.ForeignKey(Product, related_name='baskets', on_delete=models.CASCADE, default=None, null=True)
    user = models.ForeignKey(Customer, related_name='basket_lists', on_delete=models.CASCADE, default=None, null=True)


class BasketListModel(models.Model):
    basket_group_id = models.IntegerField()
    user = models.ForeignKey(Customer, related_name='basket_list', on_delete=models.CASCADE, default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Order(object):

    def __init__(self, products, basket_group, total_price):
        self.products = products
        self.basket_group = basket_group
        self.total_price = total_price




