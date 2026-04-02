from django.urls import path, include
from . import views


urlpatterns = [
    path('details/<str:word_name>', views.word_details, name='details'),
    path('details/<str:word_name>/status/change', views.change_word_status, name='change_status'),
    path('details/<str:word_name>/status/change', views.change_word_status, name='change_status'),
    path('<str:word_name>/status/mark_as_learned', views.mark_as_learned, name='mark_as_learned'),

]