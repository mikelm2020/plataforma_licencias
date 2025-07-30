from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("clientes/", views.client_list_view, name="client_list"),
    path(
        "clientes/<str:clave_cliente>/", views.client_detail_view, name="client_detail"
    ),
    path(
        "clientes/<str:clave_cliente>/add_license/",
        views.add_license_view,
        name="add_license",
    ),
    path(
        "clientes/<str:clave_cliente>/licenses/<int:licencia_id>/edit/",
        views.update_license_view,
        name="update_license",
    ),
    path(
        "clientes/<str:clave_cliente>/delete_license/<int:licencia_id>/",
        views.delete_license_view,
        name="delete_license",
    ),
]
