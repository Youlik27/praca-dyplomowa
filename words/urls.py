from django.urls import path, include
from . import views


urlpatterns = [
    path('details/<str:word_name>', views.word_details, name='details'),
    path('details/<str:word_name>/status/change', views.change_word_status, name='change_status'),
    path('collections', views.view_groups_menu, name='collection_menu'),
    path('collection/create', views.create_collection, name='create_collection'),
    path('collection/<str:collection_name>', views.manage_collection, name='manage_collection'),
    path('collection/<str:collection_name>/word/add', views.word_add, name='word_add'),
]
