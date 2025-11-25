from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from .forms import LoginForm, RegisterForm
from core.models import UserEnglishVocabulary



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
    wazneWords = UserEnglishVocabulary.objects.filter(user=request.user, study_status = 'WAZNE')
    return render(request, 'accounts/userVocabulary.html', {
        'nieZnamWords': nieZnamWords,
        'uczeSieWords': uczeSieWords,
        'znamWords': znamWords,
        'wazneWords': wazneWords,
    })