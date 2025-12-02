import requests
import re
from django.shortcuts import render
from django.utils.safestring import mark_safe


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
            system_prompt = (
            )
            full_prompt = (
                "Ty jesteś profesjonalnym słownikiem polsko-angielskim.\n"
                "Twoim zadaniem jest tworzenie słownika, tłumacząc podane przez użytkownika polskie słowa lub zdania.\n\n"
                "Instrukcje dotyczące odpowiedzi:\n"
                "1. Wszystkie tłumaczone słowa, frazy oraz przykładowe zdania (przykłady użycia) muszą być podane **wyłącznie w języku angielskim**.\n"   
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



def make_collection(request):

    context = {}

    if request.method == "POST":
        user_input = request.POST.get('prompt')

        if user_input:
            full_prompt = (
                "Jesteś programem do tworzenia kolekcji słów na temat podany przez użytkownika. "
                "Twoim zadaniem jest podanie 10-15 słów w języku angielskim oraz nazwy dla tej kolekcji. "
                "Oto jak musi wyglądać odpowiedź:\n"
                "Name:...;Words:...;\n"
                "Odtwórz ten format idealnie, co do spacji. Twoja odpowiedź ma zastąpić trzy kropki '...' odpowiednią treścią.\n"
                f"Wejście użytkownika: \"{user_input}\"\n"
                "Odpowiedź:"
            )

            raw_response, error = call_llm_api(full_prompt)

            if error:
                context['response'] = error
            else:
                context['response'] = mark_safe(raw_response)

    return render(request, 'ai/input_query.html', context)