from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from core.models import EnglishWord, UserEnglishVocabulary, WordDefinition, WordList, WordListMembership
from words.views import get_top_definitions_by_pos
@login_required
def view_word_lists(request):
    word_lists = WordList.objects.filter(owner=request.user)
    return render(request, 'wordlists/word_lists_menu.html', {'word_lists': word_lists})

@login_required
def create_word_list(request):
    word_list = WordList.objects.create(
        name='List ' + timezone.now().strftime("%y%m%d%H%M%S"),
        owner=request.user,
        icon = 'bx-list-ul'
    )
    return redirect('word_list_detail', list_id=word_list.id)

def count_words_in_list(word_list_id):
    return WordListMembership.objects.filter(word_list_id=word_list_id).count()

@login_required
def word_list_detail(request, list_id):
    word_list = get_object_or_404(WordList, id=list_id, owner=request.user)
    memberships = WordListMembership.objects.filter(word_list=word_list)
    words_data = []
    for entry in memberships:
        english_word = entry.word
        definitions = get_top_definitions_by_pos(english_word)
        words_data.append({
            'word': english_word,
            'definitions': definitions
        })
    word_count = count_words_in_list(list_id)
    return render(request, 'wordlists/manage_word_list.html', {'word_list': word_list,  'words_data': words_data, 'word_count': word_count
    })

@login_required
def delete_word_list(request, list_id):
    word_list = get_object_or_404(WordList, id=list_id, owner=request.user)
    if request.method == 'POST':
        word_list.delete()
        messages.success(request, f'Lista "{word_list.name}" została pomyślnie usunięta.')
        return redirect('word_lists_menu')
    else:
        messages.error(request, 'Coś poszło nie tak.')
        return redirect('word_list_detail', list_id=list_id)

@login_required
def add_word_to_list(request, list_id):
    word_list = get_object_or_404(WordList, id=list_id, owner=request.user)
    word_text = request.POST.get('word')
    word = get_object_or_404(EnglishWord, word=word_text)
    already_exists = WordListMembership.objects.filter(word=word, word_list=word_list).exists()
    if not already_exists:
        WordListMembership.objects.create(
            word=word,
            word_list=word_list,
            added_at=timezone.now()
        )
        messages.success(request, f'Słowo "{word.word}" zostało dodane do listy.')
    else:
        messages.error(request, 'Słowo jest już zapisane na tej liście.')
    return redirect('word_list_detail', list_id=list_id)

@login_required
def remove_word_from_list(request, list_id, word_id):
    word_list = get_object_or_404(WordList, id=list_id, owner=request.user)
    word = get_object_or_404(EnglishWord, id=word_id)
    WordListMembership.objects.filter(word_list=word_list, word=word).delete()
    return redirect('word_list_detail', list_id=word_list.id)


def update_word_list_name(request, list_id):
    new_name = request.POST.get('new_name')
    word_list = get_object_or_404(WordList, id=list_id, owner=request.user)
    word_list.name = new_name
    word_list.save()
    return redirect('word_list_detail', list_id=list_id)


def update_word_list_icon(request, list_id):
    word_list = get_object_or_404(WordList, id=list_id, owner=request.user)

    if request.method == 'POST':
        new_icon = request.POST.get('icon')

        allowed_icons = [
            'bx-list-ul',
            'bx-book',
            'bx-book-open',
            'bx-book-heart',
            'bx-brain',
            'bx-star',
            'bx-globe',
            'bx-collection',
            'bx-folder',
            'bx-note',
        ]

        if new_icon in allowed_icons:
            word_list.icon = new_icon
            word_list.save()
            messages.success(request, 'Ikona listy została zaktualizowana.')
        else:
            messages.error(request, 'Wybrano nieprawidłową ikonę.')

    return redirect('word_list_detail', list_id=word_list.id)