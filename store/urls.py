from django.urls import path

from . import views

urlpatterns = [
	#Leave as empty string for base url
	path('', views.store, name="store"),
    path('login/', views.login_page, name="login"),
    path('logOut/', views.log_out, name="logOut"),
    path('signUp/', views.signUp, name="signup"),
    path('admin/', views.admin, name="admin"),
    

	path('cart/', views.cart, name="cart"),
	path('checkout/', views.checkout, name="checkout"),
    
	path('add-coupon/', views.AddCouponView.as_view(), name='add-coupon'),
	path('update_item/', views.updateItem, name="update_item"),
	path('process_order/', views.processOrder, name="process_order"),

	path('get_categories_with_subcategories/',views.get_categories_with_subcategories,name='get_categories_with_subcategories'),
    path('filter_products/', views.filter_products, name='filter_products'),


]