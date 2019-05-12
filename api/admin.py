from django.contrib import admin

# Register your models here.
from api.models import Product, Category, Basket, BasketListModel, Customer

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Basket)
admin.site.register(BasketListModel)
admin.site.register(Customer)

