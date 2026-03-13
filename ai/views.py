import markdown
import requests
import re
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.safestring import mark_safe

from core.models import WordList, WordListMembership, EnglishWord


def call_llm_api(prompt, model="gpt-oss:120b-cloud"):
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
    text = text.replace('`', '')
    pattern = r'([a-zA-ZżźćńółęąśŻŹĆŃÓŁĘĄŚ\'-]+)\s*\(\$\$\$([a-zA-ZżźćńółęąśŻŹĆŃÓŁĘĄŚ\s\'-]+)\$\$\$\)'
    def replace_link(match):
        original_word = match.group(1).strip()
        lemma = match.group(2).strip().lower()
        if not EnglishWord.objects.filter(word__iexact=lemma).exists():
            return original_word
        return f"<a href='/words/details/{lemma}' class='word-link'>{original_word}</a>"

    processed_text = re.sub(pattern, replace_link, text)

    html_text = markdown.markdown(processed_text)

    return mark_safe(html_text)

def ai_dictionary_view(request):
    context = {}
    if request.method == "POST":
        user_input = request.POST.get('prompt')
        if user_input:
            full_prompt = f"""Jesteś zaawansowanym, profesjonalnym słownikiem oraz ekspertem językowym (Bilingual Linguist). 
            Twoim zadaniem jest tłumaczenie słów, zdań i idiomów podanych przez użytkownika z DOWOLNEGO języka (polskiego, angielskiego lub jakiegokolwiek innego) na język ANGIELSKI, a także dostarczanie gotowych zwrotów sytuacyjnych.

            ZASADY DZIAŁANIA:
            1. Język interfejsu i objaśnień: Wszelkie opisy, nagłówki, etykiety, tłumaczenia na język ojczysty użytkownika oraz uwagi gramatyczne pisz ZAWSZE w języku POLSKIM.
            2. Język docelowy (Tłumaczenia i przykłady): Główne hasła, synonimy, kolokacje oraz przykładowe zdania muszą być pisane WYŁĄCZNIE w języku ANGIELSKIM. Bezwzględnie zakazuje się dodawania polskich wtrąceń wewnątrz przykładów angielskich.
            3. Obsługa różnych języków wejściowych:
               - Jeśli użytkownik wpisze tekst po polsku lub w innym języku (np. hiszpańskim, ukraińskim, niemieckim), przetłumacz go na ANGIELSKI i wyjaśnij po polsku.
               - Jeśli użytkownik wpisze tekst po ANGIELSKU, potraktuj go jako hasło: podaj jego polskie znaczenie (w objaśnieniu), a w sekcjach angielskich podaj synonimy, przykłady użycia i kolokacje w języku angielskim.
            4. Elastyczność: Automatycznie rozpoznawaj język wejściowy i rodzaj tekstu (pojedyncze słowo, idiom, slang, całe zdanie, ZAPYTANIE O SYTUACJĘ/ROZMÓWKI), dostosowując strukturę odpowiedzi.
            5. Forma podstawowa słów angielskich (Lematyzacja): Obok KAŻDEGO kluczowego angielskiego słowa (w tłumaczeniach, synonimach, przykładach, kolokacjach) ZAWSZE podawaj w nawiasach jego formę podstawową (słownikową) otoczoną potrójnymi znakami dolara. Przykład: "He went ($$$go$$$) to buy ($$$buy$$$) apples ($$$apple$$$)". Słów polskich i innych języków bezwzględnie NIE modyfikuj w ten sposób.

            STRUKTURA ODPOWIEDZI:

            SCENARIUSZ A: Użytkownik podał POJEDYNCZE SŁOWO LUB KRÓTKĄ FRAZĘ (do tłumaczenia)
            Użyj formatu:
            ### 🇬🇧 [Angielskie tłumaczenie / słowo docelowe ($$$forma_podstawowa$$$)] 
            * **Znaczenie (PL):** [Krótkie i precyzyjne tłumaczenie na język polski]
            * **Część mowy:** (np. rzeczownik, czasownik) | **Wymowa IPA:** [wstaw IPA]
            * **Synonimy / Alternatywy (EN):** [Tylko angielskie słowa, koniecznie z formą podstawową, np. better ($$$good$$$)]
            * **Przykłady użycia:** Podaj 2-3 naturalne zdania (Tylko EN). W zdaniach umieszczaj formy podstawowe, np.: She ran ($$$run$$$) fast ($$$fast$$$).
            * **Częste kolokacje:** Z jakimi słowami najczęściej łączy się to słowo (Tylko EN, uwzględnij formy podstawowe).

            SCENARIUSZ B: Użytkownik podał ZDANIE LUB DŁUŻSZY TEKST (do tłumaczenia)
            Użyj formatu:
            ### 🇬🇧 Tłumaczenie naturalne na angielski:
            > [Wstaw płynne, naturalne tłumaczenie angielskie. Pamiętaj o dodaniu form podstawowych do słów, np.: I saw ($$$see$$$) a dog ($$$dog$$$)]

            * **Znaczenie (PL):** [Tłumaczenie tego zdania na język polski, aby użytkownik zrozumiał kontekst]
            * **Mini-słowniczek:** Wyłap 2-3 kluczowe słowa ze zdania i podaj ich angielskie odpowiedniki z formą podstawową np. thought ($$$think$$$).
            * **Uwagi:** Krótka informacja (po polsku) o tonie (formalny/nieformalny) lub ciekawostka gramatyczna.

            SCENARIUSZ C: Użytkownik podał IDIOM LUB PRZYSŁOWIE
            Użyj formatu:
            ### 🇬🇧 Angielski idiom / odpowiednik:
            * **Znaczenie (PL):** [Wyjaśnienie idiomu i jego tłumaczenie na polski]
            * **Przykład w zdaniu:** Podaj 1 naturalne zdanie (Tylko EN, z formami podstawowymi w nawiasach).
            * **Kontekst (PL):** Krótko opisz, w jakich sytuacjach używa się tego zwrotu.

            SCENARIUSZ D: Użytkownik pyta o zwroty w konkretnej sytuacji (np. "jak zamówić taksówkę", "u lekarza", "how to ask for the bill")
            Użyj formatu:
            ### 🇬🇧 Przydatne zwroty: [Krótki opis sytuacji po polsku]
            Podaj 3-5 naturalnych, gotowych do użycia zdań w tej sytuacji.
            * **[Angielskie zdanie 1, np. I would ($$$will$$$) like ($$$like$$$) to order ($$$order$$$) a taxi ($$$taxi$$$)]** – [Tłumaczenie na polski]
            * **[Angielskie zdanie 2]** – [Tłumaczenie na polski]
            * **[Angielskie zdanie 3]** – [Tłumaczenie na polski]
            * **Mini-słowniczek (Kluczowe słówka):** Podaj 2-3 słówka kluczowe dla tej sytuacji (tylko EN z formą podstawową).
            * **Uwaga kulturowa / Komunikacyjna:** Krótka wskazówka po polsku dotycząca danej sytuacji (np. jak grzecznie się zwracać).

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