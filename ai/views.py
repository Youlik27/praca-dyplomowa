import requests
import re
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.safestring import mark_safe

from core.models import WordList, WordListMembership, EnglishWord


def call_llm_api(prompt, model="deepseek-v3.1:671b-cloud"):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        json_data = response.json()

        return json_data.get('response', ''), None

    except requests.exceptions.RequestException as e:
        return None, f"Błąd zapytania do Ollama: {str(e)}"
    except Exception as e:
        return None, f"Wystąpił błąd: {str(e)}"


def make_text_clickable(text):
    if not text:
        return ""

    pattern = r'(?<!\w)([A-Za-zÀ-ž]+)(?!\w)'

    def replace_link(match):
        word = match.group(1)
        return f"<a href='/word/{word}' class='word-link'>{word}</a>"

    return mark_safe(re.sub(pattern, replace_link, text))


def ai_dictionary_view(request):
    context = {}
    if request.method == "POST":
        user_input = request.POST.get('prompt')
        if user_input:
            full_prompt = (
                "Ty jesteś profesjonalnym słownikiem polsko-angielskim.\n"
                "Twoim zadaniem jest tworzenie słownika, tłumacząc podane przez użytkownika polskie słowa lub zdania.\n\n"
                "Instrukcje dotyczące odpowiedzi:\n"
                "1. Wszystkie tłumaczone słowa, frazy oraz przykładowe zdania (przykłady użycia) muszą być podane **wyłącznie в języku angielskim**.\n"
                "2. Możesz używać języka polskiego do tworzenia opisów, etykiet lub wstępów (na przykład: \"Tłumaczenie:\", \"Przykłady użycia:\", \"Oto Twoje słowa:\").\n"
                "3. Nie dodawaj żadnych polskich wyjaśnień do samych angielskich słów.\n\n"
                f"Wejście użytkownika: \"{user_input}\"\n"
                "Odpowiedź:"
            )

            raw_response, error = call_llm_api(full_prompt)

            if error:
                context['response'] = error
            else:
                context['response'] = make_text_clickable(raw_response)

    return render(request, 'ai/ai.html', context)


def create_ai_word_list(request):
    context = {}
    if request.method == "POST":
        user_input = request.POST.get('prompt')
        if user_input:
            full_prompt = (
                    "Jesteś automatem generującym dane. Nie pisz wstępów. "
                    "Stwórz listę angielskich słówek na temat: " + user_input + ". "
                                                                                "Format: Name:NazwaListy;Words:word1,word2,word3;\n"
                                                                                "Używaj tylko pojedynczych słów, bez opisów."
            )

            raw_response, error = call_llm_api(full_prompt)

            if error:
                context['error'] = error
            else:
                match = re.search(r"Name:\s*(.*?);\s*Words:\s*(.*?)(?:;|$)", raw_response, re.DOTALL)
                if match:
                    word_list_name = match.group(1).strip()
                    words_string = match.group(2).strip()
                    words_list = [w.strip() for w in words_string.split(',') if w.strip()]

                    word_list = WordList.objects.create(
                        name=word_list_name,
                        owner=request.user
                    )

                    added_count = 0
                    for word_text in words_list:
                        english_word = EnglishWord.objects.filter(word__iexact=word_text).first()

                        if english_word:
                            WordListMembership.objects.get_or_create(
                                word=english_word,
                                word_list=word_list
                            )
                            added_count += 1

                    if added_count == 0:
                        context['error'] = "AI wygenerowało słowa, których nie ma w naszej bazie."
                    else:
                        context['success'] = "Lista została utworzona"
                        return redirect('word_list_detail', list_id=word_list.id)
                else:
                    context['error'] = "AI nie zachowało formatu. Spróbuj inaczej sformułować zapytanie."

    return render(request, 'ai/input_query.html', context)