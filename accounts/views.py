from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from .forms import LoginForm, RegisterForm
from core.models import UserEnglishVocabulary, Quiz



def login(request):
    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('home')


    return render(request, 'accounts/login.html', {'form': form})
def logout_view(request):
    logout(request)
    return redirect('home')
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('home')

    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})
@login_required(login_url='login')
def vocabulary_view(request):
    nieZnamWords = UserEnglishVocabulary.objects.filter(user=request.user, study_status = 'NIE_ZNAM')
    uczeSieWords = UserEnglishVocabulary.objects.filter(user=request.user, study_status = 'UCZE_SIE')
    znamWords = UserEnglishVocabulary.objects.filter(user=request.user, study_status = 'ZNAM')
    return render(request, 'accounts/userVocabulary.html', {
        'nieZnamWords': nieZnamWords,
        'uczeSieWords': uczeSieWords,
        'znamWords': znamWords,
    })
def last_saved_word(request):
    last_word = UserEnglishVocabulary.objects.filter(user=request.user).order_by('-added_at').first()
    if last_word is None:
        return None
    return last_word.word.word

def last_completed_quiz(request):
    last_quiz = Quiz.objects.filter(user=request.user).order_by('-created_at').first()
    if last_quiz is None:
        return None
    return f"{last_quiz.correct_count}/10"
def user_words_summary(request):
    userWords = UserEnglishVocabulary.objects.filter(user=request.user)
    unknown_words = userWords.filter(study_status='NIE_ZNAM').count()
    learning_words = userWords.filter(study_status='UCZE_SIE').count()
    known_words = userWords.filter(study_status='ZNAM').count()

    return {
        'unknown_words': unknown_words,
        'learning_words': learning_words,
        'known_words': known_words
    }
def profile_view(request):
    user = request.user
    last_word = last_saved_word(request)
    last_quiz = last_completed_quiz(request)
    word_summary = user_words_summary(request)
    return render(request, 'accounts/profile.html', {
        'user': user,
        'last_word': last_word,
        'last_quiz': last_quiz,
        'unknown_words': word_summary['unknown_words'],
        'learning_words': word_summary['learning_words'],
        'known_words': word_summary['known_words']
    })