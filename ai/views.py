from urllib.parse import quote

import markdown
import requests
import re

from django.contrib import messages
from django.http import request
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.safestring import mark_safe

from core.models import WordList, WordListMembership, EnglishWord, AssistantResponse



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
    text = text.replace('`', '')
    pattern = r'([a-zA-ZżźćńółęąśŻŹĆŃÓŁĘĄŚ\'-]+(?:\s+[a-zA-ZżźćńółęąśŻŹĆŃÓŁĘĄŚ\'-]+){0,3})[.,:;!?]?\s*\(\$\$\$([a-zA-ZżźćńółęąśŻŹĆŃÓŁĘĄŚ\s\'-]+)\$\$\$\)'
    def replace_link(match):
        original_word = match.group(1).strip()
        lemma = match.group(2).strip().lower()
        if not EnglishWord.objects.filter(word__iexact=lemma).exists():
            return original_word
        lemma_url = quote(lemma)
        return f"<a href='/words/details/{lemma}' class='word-link'>{original_word}</a>"

    processed_text = re.sub(pattern, replace_link, text)

    html_text = markdown.markdown(processed_text)

    return mark_safe(html_text)
def save_assistant_response(request, text, user_input):
    title_match = re.search(r'<title>(.*?)</title>', text)
    if title_match:
        chat_title = title_match.group(1).strip()
        clean_response = re.sub(r'<title>.*?</title>\n*', '', text).strip()
        AssistantResponse.objects.create(
            name=chat_title,
            user=request.user,
            text=clean_response,
            user_input = user_input,
        )
        return clean_response
    else:
        chat_title = 'Answer'
        AssistantResponse.objects.create(
            name=chat_title,
            user=request.user,
            text=text,
            user_input = user_input,
        )
        return text
def ai_dictionary_view(request):
    context = {}
    if request.method == "POST":
        user_input = request.POST.get('prompt')
        context['user_input'] = user_input
        if user_input:
            full_prompt = f"""Jesteś zaawansowanym, profesjonalnym słownikiem oraz ekspertem językowym (Bilingual Linguist). 
            Twoim zadaniem jest tłumaczenie słów, zdań i idiomów podanych przez użytkownika z DOWOLNEGO języka na język ANGIELSKI, a także dostarczanie gotowych zwrotów sytuacyjnych.

            ZASADY DZIAŁANIA:
            1. Język interfejsu i objaśnień: Wszelkie opisy, nagłówki, etykiety, tłumaczenia na język ojczysty użytkownika oraz uwagi gramatyczne pisz ZAWSZE w języku POLSKIM.
            2. Język docelowy (Tłumaczenia i przykłady): Główne hasła, synonimy, kolokacje oraz przykładowe zdania muszą być pisane WYŁĄCZNIE w języku ANGIELSKIM. Bezwzględnie zakazuje się dodawania polskich wtrąceń wewnątrz przykładów angielskich.
            3. Obsługa różnych języków wejściowych: Automatycznie tłumacz na angielski i wyjaśniaj po polsku.
            4. Elastyczność: Rozpoznawaj rodzaj tekstu (pojedyncze słowo, idiom, zdanie, rozmówki).
            5. Forma podstawowa: Obok ABSOLUTNIE KAŻDEGO angielskiego słowa w tekście (nawet wewnątrz pełnych zdań, pytań i przykładów!) podawaj w nawiasach jego formę podstawową otoczoną potrójnymi znakami dolara. Przykład dla zdania: "Where ($$$where$$$) is ($$$be$$$) the ($$$the$$$) check-in ($$$check-in$$$) desk ($$$desk$$$)?" To jest bezwzględny i krytyczny wymóg!            
            6. TYTUŁ DLA HISTORII (BARDZO WAŻNE): W pierwszej linijce swojej odpowiedzi ZAWSZE generuj krótki, 2-4 słowny tytuł podsumowujący zapytanie i zamknij go w tagach <title> i </title>. Przykład: <title>Słowo: Jabłko</title> lub <title>Rozmówki: U lekarza</title>. Po tagu zrób nową linię i przejdź do reszty odpowiedzi.

            STRUKTURA ODPOWIEDZI:

            <title>[Krótki tytuł dla historii]</title>

            SCENARIUSZ A: Użytkownik podał POJEDYNCZE SŁOWO LUB KRÓTKĄ FRAZĘ
            ### 🇬🇧 [Angielskie tłumaczenie / słowo docelowe ($$$forma_podstawowa$$$)] 
            * **Znaczenie (PL):** [Tłumaczenie]
            * **Część mowy:** [Część mowy] | **Wymowa IPA:** [IPA]
            * **Synonimy / Alternatywy (EN):** [Synonimy z formą podstawową]
            * **Przykłady użycia:** [Zdania EN z formą podstawową]
            * **Częste kolokacje:** [Kolokacje EN]

            SCENARIUSZ B: Użytkownik podał ZDANIE LUB DŁUŻSZY TEKST
            ### 🇬🇧 Tłumaczenie naturalne na angielski:
            > [Tłumaczenie EN z formami podstawowymi]
            * **Znaczenie (PL):** [Tłumaczenie PL]
            * **Mini-słowniczek:** [Słowa EN z formą podstawową]
            * **Uwagi:** [Ton/gramatyka]

            SCENARIUSZ C: Użytkownik podał IDIOM LUB PRZYSŁOWIE
            ### 🇬🇧 Angielski idiom / odpowiednik:
            * **Znaczenie (PL):** [Tłumaczenie PL]
            * **Przykład w zdaniu:** [Zdanie EN z formami podstawowymi]
            * **Kontekst (PL):** [Kontekst użycia]

            SCENARIUSZ D: Rozmówki (np. w sklepie)
            ### 🇬🇧 Przydatne zwroty: [Opis sytuacji]
            * **[Zdanie 1 EN]** – [Tłumaczenie PL]
            * **Mini-słowniczek:** [Słowa kluczowe]
            * **Uwaga kulturowa:** [Wskazówka]

            Wejście użytkownika: "{user_input}"
            Odpowiedź:"""

            raw_response, error = call_llm_api(full_prompt)

            if error:
                context['response'] = error
            else:
                clean_text = save_assistant_response(request, raw_response,user_input)
                context['response'] = make_text_clickable(clean_text)
    elif request.method == "GET":
        chat_id = request.GET.get('chat_id')
        if chat_id:
            old_chat = get_object_or_404(AssistantResponse, id=chat_id, user=request.user)
            context['response'] = make_text_clickable(old_chat.text)
            context['user_input'] = old_chat.user_input
    context['all_user_chats'] = AssistantResponse.objects.filter(user=request.user).order_by('-id')
    return render(request, 'ai/assistant.html', context)
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
                                                                                "Nazwa Listy (Name) MUSI zawierać spacje między słowami (np. 'My Trip To London' a nie 'MyTripToLondon')."

            )

            raw_response, error = call_llm_api(full_prompt)

            if error:
                context['error'] = error
            else:
                match = re.search(r"Name:\s*(.*?);\s*Words:\s*(.*?)(?:;|$)", raw_response, re.DOTALL)
                if match:
                    word_list_name = match.group(1).strip()
                    words_string = match.group(2).strip().lower()
                    words_list = [w.strip() for w in words_string.split(',') if w.strip()]

                    word_list = WordList.objects.create(
                        name=word_list_name,
                        owner=request.user,
                        icon='bx-list-ul',
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
                        messages.error(request, 'AI wygenerowało słowa, których nie ma w naszej bazie lub AI nie zrozumiało pytanie.')

                    else:
                        messages.success(request, 'Lista została utworzona.')
                        return redirect('word_list_detail', list_id=word_list.id)
                else:
                    messages.error(request,'AI nie zachowało formatu. Spróbuj inaczej sformułować zapytanie.')

    return render(request, 'ai/input_query.html')