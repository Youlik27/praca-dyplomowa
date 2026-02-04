from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_quiz_menu, name='view_quiz_menu'),
    path('repeat_and_learn', views.create_quiz_repeat_and_learn, name='create_quiz_repeat_and_learn'),

]