from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_quiz_menu, name='view_quiz_menu'),
    path('repeat_and_learn/', views.create_quiz_repeat_and_learn, name='create_quiz_repeat_and_learn'),
    path('quiz/<int:quiz_id>/<int:question_number>/', views.view_quiz, name='view_quiz'),
    path('quiz/<int:quiz_id>/<int:question_number>/check_answer/', views.check_answer, name='check_answer'),
    path('quiz/<int:quiz_id>/finish', views.quiz_finished, name='quiz_finished'),

]