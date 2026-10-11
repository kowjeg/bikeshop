from django.urls import path

from .views import review_create

app_name = 'reviews'

urlpatterns = [
    path('product/<slug:slug>/review/', review_create, name='create'),
]