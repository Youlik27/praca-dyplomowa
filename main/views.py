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
    exact_matches= EnglishWord.objects.filter(word=query)
    partial_matches = EnglishWord.objects.filter(word__icontains=query).order_by('frequency')
    words = list(exact_matches) + [w for w in partial_matches if w not in exact_matches]
    words = [w for w in words if len(w.word) <= 30][:5]
    words_data = [{'word': w.word} for w in words]
    return JsonResponse(words_data, safe=False)
