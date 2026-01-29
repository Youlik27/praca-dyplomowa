from django.urls import path, include
from . import views


urlpatterns = [
    path('profile', views.profile_view, name='profile_view'),
    path('login', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register', views.register, name='register'),
    path('vocabulary/', views.vocabulary_view, name='vocabulary'),
]
