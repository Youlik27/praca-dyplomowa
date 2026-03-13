from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_word_lists, name='word_lists_menu'),
    path('create', views.create_word_list, name='create_word_list'),
    path('<int:list_id>', views.word_list_detail, name='word_list_detail'),
    path('<int:list_id>/delete', views.delete_word_list, name='delete_word_list'),
    path('<int:list_id>/word/add', views.add_word_to_list, name='add_word_to_list'),
    path('<int:list_id>/word/<int:word_id>/remove', views.remove_word_from_list, name='remove_word_from_list'),
    path('<int:list_id>/update/name', views.update_word_list_name, name='update_word_list_name'),
    path('<int:list_id>/update/icon', views.update_word_list_icon, name='update_word_list_icon'),

]