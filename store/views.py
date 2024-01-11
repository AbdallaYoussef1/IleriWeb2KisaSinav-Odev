from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
import json
import datetime
from django.views import View
from .models import *
from .templates import *
from .utils import cookieCart, cartData, guestOrder
from django.views.decorators.csrf import csrf_protect
from .forms import CreateUser
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from .forms import CouponForm
from django.core import serializers

# @login_required(login_url='login')
def store(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    user = request.user.is_authenticated

    products = Product.objects.all()
    categories = Category.objects.all()

    context = {'products': products, 'cartItems': cartItems, 'categories': categories, 'is_authenticated': user }

    # Search for products based on product_name
    if request.POST.get("product_name"):
        product_name = request.POST.get("product_name")
        try:
            # Filter products based on the search query
            searched_products = Product.objects.filter(name__icontains=product_name)

            # Serialize the searched products and return as JSON response
            serialized_search_data = [
                {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'imageURL': product.imageURL,
                    # Add more fields you want to display
                }
                for product in searched_products
            ]

            # Add the searched products to the context with a different key
            context['searched_products'] = serialized_search_data

        except Product.DoesNotExist:
            context['error'] = 'Products not found'

    if request.POST.get("subcategory"):
        subcategory_name = request.POST.get('subcategory')
        try:
            # Retrieve the subcategory based on the received name
            subcategory = SubCategory.objects.get(subcategoryName=subcategory_name)

            # Filter products associated with the selected subcategory
            filtered_products = Product.objects.filter(subcategories=subcategory)

            # Serialize the filtered products and return as JSON response
            serialized_data = [
                {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'imageURL': product.imageURL,
                    # Add more fields you want to display
                }
                for product in filtered_products
            ]

            # Add the filtered products to the context with a different key
            context['filtered_products'] = serialized_data

        except SubCategory.DoesNotExist:
            context['error'] = 'Subcategory not found'
        except Product.DoesNotExist:
            context['error'] = 'Products not found'


     # Handle sorting direction
    if request.POST.get("flexRadioDefault"):
        sortType = request.POST.get("flexRadioDefault")

        if sortType == "asc":
            # Sort products by price in ascending order
            products = Product.objects.all().order_by('price')
            context['sorted_products'] = products
        
        elif sortType == "desc":
            # Sort products by price in descending order
            products = Product.objects.all().order_by('-price')
            context['sorted_products'] = products

    return render(request, 'store/Store.html', context)



def login_page(request):
	if request.user.is_authenticated:
		return redirect('store')
	else:
		if request.method == "POST":
			username = request.POST.get('username')
			password = request.POST.get('password')
			user = authenticate(username=username, password=password)

			if user is not None:
				login(request, authenticate(username=username, password=password))
				return redirect('store')  # Redirect to a different view after successful login
			else:
				messages.info(request, 'Invalid credentials')
				return render(request, 'store/loginPage.html', {})
		else:
			return render(request, 'store/loginPage.html', {})
	
def log_out(request):
	logout(request)
	return redirect('login')
	

@csrf_protect
def signUp(request):
	if request.user.is_authenticated:
		return redirect('store')
    # Instantiate the form for GET requests
	else:
		form = CreateUser()
		if request.method == 'POST':
			form_post = CreateUser(request.POST)
			if form_post.is_valid():
				user = form_post.cleaned_data.get('username')  # Access cleaned data after validating the form
				form_post.save()
				messages.success(request, "Congratulations, " + user + ", you signed up successfully")
				return redirect('login')# Redirect to the login page after successful signup

			# If form is invalid, handle errors
			else:
				# Pass the form with errors to the context
				context = {'form': form_post}
				return render(request, 'store/signUp.html', context)

		context = {'form': form}  # Pass the initial form to the context
		return render(request, 'store/signUp.html', context)


@login_required(login_url='login')
def cart(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    user = request.user.is_authenticated

    context = {'items': items, 'order': order, 'cartItems': cartItems, 'is_authenticated': user}
    return render(request, 'store/cart.html', context)

def admin(request):
    if request.user.is_authenticated and request.user.is_staff:
        # If the user is authenticated and is a staff member, redirect to the admin page
        return redirect('admin:index')


@login_required(login_url='login')
def checkout(request):
    data = cartData(request)
    
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    user = request.user.is_authenticated

    context = {'items': items, 'order': order, 'cartItems': cartItems, 'couponform': CouponForm, 'is_authenticated': user}
    return render(request, 'store/checkout.html', context)


@login_required(login_url='login')
def updateItem(request):
    # Move the productId definition to the beginning
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)

    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    # Move the productId definition above this line
    data = {'message': 'Item updated successfully'}

    return JsonResponse(data)

@login_required(login_url='login')
def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)

def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("checkout")
	

def get_categories_with_subcategories(request):
    try:
        categories = Category.objects.prefetch_related('subcategory_set').all()

        serialized_data = []

        for category in categories:
            category_data = {
                'category_name': category.categoryName,
                'subcategories': [
                    {
                        'subcategory_name': subcategory.subcategoryName,
                        'subcategory_description': subcategory.description,
                    }
                    for subcategory in category.subcategory_set.all()
                ]
            }
            serialized_data.append(category_data)

        return JsonResponse({'categories': serialized_data})
    
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Categories not found'}, status=404)
	
def filter_products(request):
    try:
        subcategory_name = request.POST.get('subcategory')
        # Retrieve the subcategory based on the received name
        subcategory = SubCategory.objects.get(subcategoryName=subcategory_name)

        # Filter products associated with the selected subcategory
        filtered_products = Product.objects.filter(subcategories=subcategory)

        # Serialize the filtered products and return as JSON response
        serialized_data = [
            {
                'name': product.name,
                'price': product.price,
                'imageURL': product.imageURL,
                # Add more fields you want to display
            }
            for product in filtered_products
        ]
        return render(request, 'store/Store.html', {"filtered_products": serialized_data})
        # return JsonResponse({'filtered_products': serialized_data})

    except SubCategory.DoesNotExist:
        return JsonResponse({'error': 'Subcategory not found'}, status=404)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Products not found'}, status=404)

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
           try:
             code = form.cleaned_data.get('code')
             user = get_object_or_404(User, username='abdo')
             customer = get_object_or_404(Customer, user=user)
             order = get_object_or_404(Order, customer=customer, complete=False)
             order.coupon = get_coupon(self.request, code)
             order.save()
             messages.success(self.request, "Successfully added coupon")
             return redirect("checkout")
           except ObjectDoesNotExist:
             messages.info(self.request, "You do not have an active order")
             return redirect("checkout")
