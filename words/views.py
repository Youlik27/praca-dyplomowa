from idlelib.pyparse import trans

from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect, get_object_or_404

from core.models import EnglishWord, UserEnglishVocabulary, WordDefinition, WordList, WordListMembership
from django.utils import timezone


def get_top_definitions_by_pos(word):
    definitions = WordDefinition.objects.filter(
        english_word=word.id
    ).order_by('polish_word_id', '-translation_score').distinct('polish_word_id')

    sorted_definitions = sorted(
        definitions,
        key=lambda x: x.translation_score if x.translation_score is not None else float('-inf'),
        reverse=True
    )

    top_definitions_by_pos = {}

    for d in sorted_definitions:
        pos = d.part_of_speech
        if pos not in top_definitions_by_pos:
            top_definitions_by_pos[pos] = []
        if len(top_definitions_by_pos[pos]) < 3:
            top_definitions_by_pos[pos].append(d)

    return top_definitions_by_pos


def get_user_word_status(user, word):
    if not user.is_authenticated:
        return None

    try:
        vocab_entry = UserEnglishVocabulary.objects.get(word=word.id, user=user)
        return vocab_entry.study_status
    except UserEnglishVocabulary.DoesNotExist:
        return None
def word_details(request, word_name):
    word = get_object_or_404(EnglishWord, word=word_name)
    if not word:
        return render(request, 'main/not_found.html', {'searched_word': word_name})
    definitions = get_top_definitions_by_pos(word)
    word_status = get_user_word_status(request.user, word)
    return render(request, 'words/wordDetails.html', {
        'word': word,
        'definitions': definitions,
        'word_status': word_status
    })
@login_required(login_url='/account/login/')
def change_word_status(request, word_name):
    new_status = request.POST.get('status')
    next_url = request.POST.get('next')
    if request.user.is_authenticated:
        word = EnglishWord.objects.get(word=word_name)
        try:
            word_in_vocabulary = UserEnglishVocabulary.objects.get(word=word.id, user=request.user)
            word_in_vocabulary.study_status = new_status
            word_in_vocabulary.save()
        except UserEnglishVocabulary.DoesNotExist:
            UserEnglishVocabulary.objects.create(
                user=request.user,
                word=word,
                study_status=new_status,
                last_reviewed_at=timezone.now(),
                added_at=timezone.now(),
            )
    if next_url:
        return redirect(next_url)
    else:
        return redirect('details', word_name=word_name)