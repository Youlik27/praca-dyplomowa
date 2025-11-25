from idlelib.pyparse import trans

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from core.models import EnglishWord, UserEnglishVocabulary, WordDefinition
from django.utils import timezone


def word_details(request, word_name):
    verbs = WordDefinition.objects.none()
    word = EnglishWord.objects.get(word=word_name)
    word_id = word.id
    if not word_name.startswith("to "):
        try:
            word_with_to = EnglishWord.objects.get(word="to " + word_name)
            word_with_to_id = word_with_to.id
            verbs = WordDefinition.objects.filter(english_word=word_with_to_id, polish_word__frequency__gte=0).order_by(
                'polish_word_id', '-polish_word__frequency').distinct('polish_word_id')

        except EnglishWord.DoesNotExist:
            word_with_to = None
    else:
        verbs = WordDefinition.objects.filter(
            english_word=word_id,
            polish_word__frequency__gte=0
        ).order_by('polish_word_id', '-polish_word__frequency').distinct('polish_word_id')
    # status słowa
    word_in_vocabulary = None
    if request.user.is_authenticated:
        user_id = request.user.id
        word_in_vocabulary = UserEnglishVocabulary.objects.get(word=word_id, user=user_id)
        word_in_vocabulary = word_in_vocabulary.study_status

    definitions_without_to= WordDefinition.objects.filter(english_word=word_id, polish_word__frequency__gte=0).order_by('polish_word_id', '-polish_word__frequency').distinct('polish_word_id')
    adjectives = sorted(definitions_without_to.filter(pos='adj'), key=lambda x: x.polish_word.frequency, reverse=True)
    nouns = sorted(definitions_without_to.filter(pos='noun'), key=lambda x: x.polish_word.frequency, reverse=True)
    adverbs = sorted(definitions_without_to.filter(pos='adv'), key=lambda x: x.polish_word.frequency, reverse=True)
    conjunctions = sorted(definitions_without_to.filter(pos='conj'), key=lambda x: x.polish_word.frequency,reverse=True)
    determiners = sorted(definitions_without_to.filter(pos='det'), key=lambda x: x.polish_word.frequency, reverse=True)
    prepositions = sorted(definitions_without_to.filter(pos='prep'), key=lambda x: x.polish_word.frequency,reverse=True)
    pronouns = sorted(definitions_without_to.filter(pos='pron'), key=lambda x: x.polish_word.frequency, reverse=True)
    verbs = sorted(verbs, key=lambda x: x.polish_word.frequency, reverse=True)
    if not definitions_without_to:
        definitions = WordDefinition.objects.filter(english_word=word_id).distinct('polish_word_id')
    return render(request, 'words/wordDetails.html', {
        'word': word,
        'adjectives': adjectives,
        'nouns': nouns,
        'adverbs': adverbs,
        'conjunctions': conjunctions,
        'determiners': determiners,
        'prepositions': prepositions,
        'pronouns': pronouns,
        'verbs': verbs,
        'word_status': word_in_vocabulary}

                  )
@login_required(login_url='/account/login/')
def change_word_status(request, word_name):
    new_status = request.POST.get('status')
    user_id = request.user.id
    if user_id is not None:
        word = EnglishWord.objects.get(word=word_name)
        try:
            word_in_vocabulary = UserEnglishVocabulary.objects.get(word=word.id, user=user_id)
            word_in_vocabulary.study_status = new_status
            word_in_vocabulary.save()
        except UserEnglishVocabulary.DoesNotExist:
            UserEnglishVocabulary.objects.create(
                user=user_id,
                word=word,
                study_status=new_status,
                last_reviewed_at=timezone.now(),
                added_at=timezone.now(),
            )
            return redirect('details', word_name)
    return redirect('details', word_name=word_name)

