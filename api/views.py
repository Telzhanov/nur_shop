from django.http import Http404
from django.shortcuts import render

# Create your views here.

from rest_framework import generics
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from api.models import Product, Category, Basket, Customer, BasketListModel, Order
from api.serializers import ProductSerializer, CategorySerializer, CategoryDetailSerializer, CustomerSerializer, \
    AddProductSerializer, BasketSerializer, CustomerAuthSerializer, OrderSerializer


class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class CategoryList(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer



@api_view(['POST'])
def login(request):
    serializer = CustomerAuthSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data.get('customer')
    serializer = CustomerSerializer(user)
    token, created = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    user = request.auth.user
    token = Token.objects.get(user=user)
    token.delete()
    serializer = CustomerSerializer(user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_order(request):
    user = request.auth.user
    customer = Customer.objects.get(id=user.id)
    if customer.basket_free:
        return Response({
            'message':'Basket empty'
        })
    customer.basket_free = True
    customer.save()
    basket_list = BasketListModel.objects.filter(user=customer).order_by('basket_group_id')
    size = len(basket_list)
    basket_group = basket_list[size - 1].basket_group_id
    basket_products = Basket.objects.filter(basket_group_id=basket_group, user=customer)
    serializer = BasketSerializer(basket_products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_history(request):
    user = request.auth.user
    customer = Customer.objects.get(id=user.id)
    if customer.basket_free:
        basket_list = BasketListModel.objects.filter(user=customer).order_by('basket_group_id')
        orders = []
        for basket_group in basket_list:
            basket_products = Basket.objects.filter(basket_group_id=basket_group.basket_group_id, user=customer)
            total_price = 0
            products = []
            for basket in basket_products:
                products.append(basket.product)
                total_price += basket.product.price * basket.quantity
            order = Order(products=products, basket_group=basket_group, total_price=total_price)
            orders.append(order)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    else:
        basket_list = BasketListModel.objects.filter(user=customer).order_by('basket_group_id')
        basket_group_it = basket_list[len(basket_list)-2].basket_group_id
        basket_group = basket_list[len(basket_list)-2]
        orders = []
        for it in range(1, basket_group_it + 1):
            basket_products = Basket.objects.filter(basket_group_id=it, user=customer)
            total_price = 0
            products = []
            for basket in basket_products:
                products.append(basket.product)
                total_price += basket.product.price * basket.quantity

            order = Order(products=products, basket_group=basket_group, total_price=total_price)
            orders.append(order)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)



class CategoryDetail(APIView):

    def get_object(self, pk):
        try:
            return Category.objects.get(id=pk)
        except Category.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        category = self.get_object(pk)
        serializer = CategoryDetailSerializer(category)
        return Response(serializer.data)

    def delete(self, pk):
        category = self.get_object(pk)
        serializer = CategorySerializer(category)
        category.delete()
        return Response(serializer.data)



class BasketList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.auth.user
        customer = Customer.objects.get(id=user.id)
        if customer.basket_free:
            return Response({
                'message': 'basket free'
            })
        else:
            basket_list = BasketListModel.objects.filter(user=customer).order_by('basket_group_id')
            size = len(basket_list)
            basket_group = basket_list[size-1].basket_group_id
            basket_products = Basket.objects.filter(basket_group_id=basket_group, user=customer)
            total_price = 0
            for basket in basket_products:
                total_price += basket.product.price * basket.quantity
            serializer = BasketSerializer(basket_products, many=True)
            return Response({
                'products': serializer.data,
                'total_price': total_price
            })

    def post(self, request):
        product_id = AddProductSerializer(data=request.data)
        if product_id.is_valid():
            try:
                product = Product.objects.get(id=product_id.data.get('product_id'))
                user = request.auth.user
                customer = Customer.objects.get(id=user.id)
                if customer.basket_free:
                    basket_list = BasketListModel.objects.filter(user=customer).order_by('basket_group_id')
                    if basket_list:
                        size = len(basket_list)
                        basket_group = basket_list[size-1].basket_group_id
                        basket_group += 1
                        new_basket_list = BasketListModel(basket_group_id=basket_group, user=customer)
                        new_basket_list.save()
                        basket = Basket(quantity=1, basket_group_id=basket_group, product=product, user=customer)
                        basket.save()
                        customer.basket_free = False
                        customer.save()
                        serializer = BasketSerializer(basket)
                        return Response(serializer.data)
                    else:
                        new_basket_list = BasketListModel(basket_group_id=1, user=customer)
                        new_basket_list.save()
                        basket = Basket(quantity=1, basket_group_id=1, product=product, user=customer)
                        basket.save()
                        customer.basket_free = False
                        customer.save()
                        serializer = BasketSerializer(basket)
                        return Response(serializer.data)
                else:
                    basket_list = BasketListModel.objects.filter(user=customer).order_by('basket_group_id')
                    size = len(basket_list)
                    basket_group = basket_list[size - 1].basket_group_id
                    baskets = Basket.objects.filter(basket_group_id=basket_group, user=customer)
                    for basket in baskets:
                        if basket.product.id == product.id:
                            basket.quantity += 1
                            basket.save()
                            serializer = BasketSerializer(basket)
                            return Response(serializer.data)
                    basket = Basket(quantity=1, basket_group_id=basket_group, product=product, user=customer)
                    basket.save()
                    customer.basket_free = False
                    customer.save()
                    serializer = BasketSerializer(basket)
                    return Response(serializer.data)
            except Product.DoesNotExist:
                raise Http404
        return Response(product_id.errors)
