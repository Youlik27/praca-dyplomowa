from django.db.models.functions import Length
from django.http import JsonResponse
from django.shortcuts import render
from core.models import PolishWord, UserEnglishVocabulary, EnglishWord


# Create your views here.
def index(request):
    return render(request, 'main/home.html')

def search(request):
    query = request.GET.get('query', '').strip()
    if not query:
        return JsonResponse([], safe=False)
    matches = EnglishWord.objects.filter(word__icontains=query).order_by(Length('word'))[:10]

    words_data = [{'word': w.word, 'id': w.id} for w in matches]
    return JsonResponse(words_data, safe=False)
