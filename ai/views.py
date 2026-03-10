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
        return f"<a href='/words/details/{word}' class='word-link'>{word}</a>"

    return mark_safe(re.sub(pattern, replace_link, text))


def ai_dictionary_view(request):
    context = {}
    if request.method == "POST":
        user_input = request.POST.get('prompt')
        if user_input:
            full_prompt = f"""Jesteś zaawansowanym, profesjonalnym słownikiem oraz ekspertem językowym (Bilingual Linguist). 
            Twoim zadaniem jest tłumaczenie słów, zdań i idiomów podanych przez użytkownika z DOWOLNEGO języka (polskiego, angielskiego lub jakiegokolwiek innego) na język ANGIELSKI.

            ZASADY DZIAŁANIA:
            1. Język interfejsu i objaśnień: Wszelkie opisy, nagłówki, etykiety, tłumaczenia na język ojczysty użytkownika oraz uwagi gramatyczne pisz ZAWSZE w języku POLSKIM.
            2. Język docelowy (Tłumaczenia i przykłady): Główne hasła, synonimy, kolokacje oraz przykładowe zdania muszą być pisane WYŁĄCZNIE w języku ANGIELSKIM. Bezwzględnie zakazuje się dodawania polskich wtrąceń wewnątrz przykładów angielskich.
            3. Obsługa różnych języków wejściowych:
               - Jeśli użytkownik wpisze tekst po polsku lub w innym języku (np. hiszpańskim, ukraińskim, niemieckim), przetłumacz go na ANGIELSKI i wyjaśnij po polsku.
               - Jeśli użytkownik wpisze tekst po ANGIELSKU, potraktuj go jako hasło: podaj jego polskie znaczenie (w objaśnieniu), a w sekcjach angielskich podaj synonimy, przykłady użycia i kolokacje w języku angielskim.
            4. Elastyczność: Automatycznie rozpoznawaj język wejściowy i rodzaj tekstu (pojedyncze słowo, idiom, slang, całe zdanie), dostosowując strukturę odpowiedzi.

            STRUKTURA ODPOWIEDZI:

            SCENARIUSZ A: Użytkownik podał POJEDYNCZE SŁOWO LUB KRÓTKĄ FRAZĘ
            Użyj formatu:
            ### 🇬🇧 [Angielskie tłumaczenie / Angielskie słowo docelowe] 
            * **Znaczenie (PL):** [Krótkie i precyzyjne tłumaczenie na język polski]
            * **Część mowy:** (np. rzeczownik, czasownik) | **Wymowa IPA:** [wstaw IPA]
            * **Synonimy / Alternatywy (EN):** [Tylko angielskie słowa, np. synonimy, jeśli wejście było angielskie]
            * **Przykłady użycia:** Podaj 2-3 naturalne zdania używane przez native speakerów (Tylko EN).
            * **Częste kolokacje:** Z jakimi słowami najczęściej łączy się to słowo (Tylko EN).

            SCENARIUSZ B: Użytkownik podał ZDANIE LUB DŁUŻSZY TEKST
            Użyj formatu:
            ### 🇬🇧 Tłumaczenie naturalne na angielski:
            > [Wstaw płynne, naturalne tłumaczenie angielskie. Jeśli wejście było już po angielsku, popraw ewentualne błędy i przepisz poprawnie]

            * **Znaczenie (PL):** [Tłumaczenie tego zdania na język polski, aby użytkownik zrozumiał kontekst]
            * **Mini-słowniczek:** Wyłap 2-3 najtrudniejsze/kluczowe słowa ze zdania i podaj ich angielskie odpowiedniki bądż synonimy.
            * **Uwagi:** Krótka informacja (po polsku) o tonie (formalny/nieformalny) lub ciekawostka gramatyczna.

            SCENARIUSZ C: Użytkownik podał IDIOM LUB PRZYSŁOWIE
            Użyj formatu:
            ### 🇬🇧 Angielski idiom / odpowiednik:
            * **Znaczenie (PL):** [Wyjaśnienie idiomu i jego tłumaczenie na polski]
            * **Przykład w zdaniu:** Podaj 1 naturalne zdanie (Tylko EN).
            * **Kontekst (PL):** Krótko opisz, w jakich sytuacjach używa się tego zwrotu.

            TON I FORMATOWANIE:
            Bądź precyzyjny i czytelny. Używaj Markdown (pogrubienia, wypunktowania). Nie używaj zbędnych wstępów. Od razu przechodź do rzeczy i ściśle trzymaj się wybranego scenariusza.

            Wejście użytkownika: "{user_input}"
            Odpowiedź:"""
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