from django.urls import path, include
from . import views


urlpatterns = [
    path('assistant/', views.ai_view, name='ai_query'),

]
