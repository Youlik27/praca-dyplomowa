from django.urls import path, include
from . import views


urlpatterns = [
    path('details/<str:word_name>', views.word_details, name='details'),
    path('details/<str:word_name>/status/change', views.change_word_status, name='change_status'),
    path('collections', views.view_groups_menu, name='groups_menu'),
]
