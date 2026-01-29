from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.ai_dictionary_view, name='ai_query'),
    path('make/collection', views.create_ai_word_list, name='ai_collection'),
]
