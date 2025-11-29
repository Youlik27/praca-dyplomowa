from idlelib.pyparse import trans

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from core.models import EnglishWord, UserEnglishVocabulary, WordDefinition, WordGroup
from django.utils import timezone


def word_details(request, word_name):
    word = get_object_or_404(EnglishWord, word=word_name)
    word_id = word.id

    definitions = WordDefinition.objects.filter( english_word=word_id,).order_by('polish_word_id', '-translation_score').distinct('polish_word_id')
    definitions = sorted(definitions, key=lambda x: x.translation_score  if x.translation_score is not None else float('-inf'), reverse=True)
    top_definitions_by_pos = {}
    for d in definitions:
        pos = d.part_of_speech
        if pos not in top_definitions_by_pos:
            top_definitions_by_pos[pos] = d

    word_status = None
    if request.user.is_authenticated:
        try:
            vocab_entry = UserEnglishVocabulary.objects.get(word=word_id, user=request.user)
            word_status = vocab_entry.study_status
        except UserEnglishVocabulary.DoesNotExist:
            word_status = None

    return render(request, 'words/wordDetails.html', {
        'word': word,
        'definitions': top_definitions_by_pos,
        'word_status': word_status
    })
@login_required(login_url='/account/login/')
def change_word_status(request, word_name):
    new_status = request.POST.get('status')
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
            return redirect('details', word_name)
    return redirect('details', word_name=word_name)

def view_groups_menu(request):
    groups = WordGroup.objects.filter(owner=request.user)
    return render(request, 'words/groupsMenu.html', {'groups': groups})
