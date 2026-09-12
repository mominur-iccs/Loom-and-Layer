from django.urls import path

from . import views

app_name = "hoodie_app"

urlpatterns = [
    path("", views.home, name="home"),
    path("select/", views.select_options, name="select_options"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/<int:order_id>/success/", views.order_success, name="order_success"),
]