from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.ai_dictionary_view, name='ai_query'),
    path('make/collection', views.make_collection, name='ai_collection'),
]
