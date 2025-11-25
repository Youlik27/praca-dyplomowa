import re
from django.contrib.sites import requests
from django.shortcuts import render
from django.utils.safestring import mark_safe


def ai_view(request):
    context = {}

    if request.method == "POST":
        prompt = request.POST.get('prompt')

        if prompt:
            url = "http://localhost:11434/api/generate"

            formatted_prompt = (
                "Ty jesteś profesjonalnym słownikiem polsko-angielskim.\n"
                "Twoim zadaniem jest tworzenie słownika, tłumacząc podane przez użytkownika polskie słowa lub zdania.\n\n"
                "Instrukcje dotyczące odpowiedzi:\n"
                "1. Wszystkie tłumaczone słowa, frazy oraz przykładowe zdania (przykłady użycia) muszą być podane **wyłącznie w języku angielskim**.\n"
                "2. Możesz używać języka polskiego do tworzenia opisów, etykiet lub wstępów (na przykład: \"Tłumaczenie:\", \"Przykłady użycia:\", \"Oto Twoje słowa:\").\n"
                "3. Nie dodawaj żadnych polskich wyjaśnień do samych angielskich słów.\n\n"
                f"Wejście użytkownika: \"{prompt}\"\n"
                "Odpowiedź:"
            )

            payload = {
                "model": "deepseek-v3.1:671b-cloud",
                "prompt": formatted_prompt,
                "stream": False
            }

            try:

                response = requests.post(url, json=payload)
                response.raise_for_status()

                json_data = response.json()
                raw_text = json_data.get('response', '')


                pattern = r'(?<!\w)([A-Za-zÀ-ž]+)(?!\w)'

                def replace_link(match):
                    word = match.group(1)
                    return f"<a href='/word/{word}' class='word-link'>{word}</a>"

                linked_text = re.sub(pattern, replace_link, raw_text)

                context['response'] = mark_safe(linked_text)

            except requests.exceptions.RequestException as e:
                context['response'] = f"Błąd zapytania do Ollama: {str(e)}"
            except Exception as e:
                context['response'] = f"Wystąpił błąd: {str(e)}"

    return render(request, 'ai.html', context)