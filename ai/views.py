import os
import re
import requests
import markdown
import spacy
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.safestring import mark_safe

from core.models import WordList, WordListMembership, EnglishWord, AssistantResponse

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download

    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


def call_llm_api(system_prompt, user_prompt, model="openai/gpt-oss-120b"):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "stream": False
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        json_data = response.json()
        result_text = json_data.get('choices', [])[0].get('message', {}).get('content', '')
        return result_text, None
    except requests.exceptions.RequestException as e:
        error_details = response.text if 'response' in locals() else str(e)
        return None, f"Błąd zapytania do API: {error_details}"
    except Exception as e:
        return None, f"Wystąpił błąd: {str(e)}"


def process_english_block(match):
    english_text = match.group(1)
    doc = nlp(english_text)
    processed_pieces = []

    for token in doc:
        word_text = token.text
        ws = token.whitespace_
        lemma = token.lemma_.lower()

        if word_text.isalpha():
            if EnglishWord.objects.filter(word__iexact=lemma).exists():
                lemma_url = quote(lemma)
                link = f"<a href='/words/details/{lemma_url}' class='word-link'>{word_text}</a>"
                processed_pieces.append(link + ws)
            else:
                processed_pieces.append(word_text + ws)
        else:
            processed_pieces.append(word_text + ws)

    return "".join(processed_pieces)


def make_text_clickable(text):
    if not text:
        return ""

    processed_text = re.sub(r'<en>(.*?)</en>', process_english_block, text, flags=re.DOTALL)

    html_text = markdown.markdown(processed_text, extensions=['extra', 'sane_lists'])

    return mark_safe(f'<div class="ai-response-container">{html_text}</div>')


def save_assistant_response(request, text, user_input):
    title_match = re.search(r'<title>(.*?)</title>', text)
    if title_match:
        chat_title = title_match.group(1).strip()
        clean_response = re.sub(r'<title>.*?</title>\n*', '', text).strip()
        AssistantResponse.objects.create(
            name=chat_title,
            user=request.user,
            text=clean_response,
            user_input=user_input,
        )
        return clean_response
    else:
        chat_title = 'Answer'
        AssistantResponse.objects.create(
            name=chat_title,
            user=request.user,
            text=text,
            user_input=user_input,
        )
        return text

@login_required
def ai_dictionary_view(request):
    context = {}
    if request.method == "POST":
        user_input = request.POST.get('prompt')
        context['user_input'] = user_input
        if user_input:
            system_prompt = """Jesteś zaawansowanym, profesjonalnym słownikiem oraz ekspertem językowym (Bilingual Linguist).
Twoim zadaniem jest tłumaczenie słów, zdań i idiomów z DOWOLNEGO języka na język ANGIELSKI oraz wyjaśnianie zasad gramatyki.

ABSOLUTNIE KRYTYCZNE ZASADY:
1. JĘZYK: Wszystkie wyjaśnienia, nagłówki, komentarze i tłumaczenia pisz ZAWSZE po POLSKU.
2. TYTUŁ: Twoja odpowiedź MUSI bezwzględnie zaczynać się od tagu <title>Krótki Tytuł</title> w pierwszej linijce.
3. ZNACZNIK ANGIELSKIEGO (NAJWAŻNIEJSZA ZASADA): Absolutnie każdy angielski tekst (pojedyncze słowa, całe zdania, synonimy, przykłady) MUSISZ zamykać w tagach <en> i </en>.
   - ŹLE: I went to the store.
   - DOBRZE: <en>I went to the store.</en>
   - ŹLE: Synonimem jest apple.
   - DOBRZE: Synonimem jest <en>apple</en>.

STRUKTURA ODPOWIEDZI:
<title>[Twój krótki tytuł]</title>
[Wybierz i zastosuj JEDEN z poniższych scenariuszy dopasowany do zapytania]

SCENARIUSZ A: Pojedyncze słowo lub krótka fraza
### <en>[Angielskie tłumaczenie]</en> 
* **Znaczenie (PL):** [Tłumaczenie]
* **Część mowy:** [Część mowy] | **Wymowa IPA:** [IPA]
* **Synonimy / Alternatywy:** <en>[Synonimy]</en>
* **Przykłady użycia:** 
  - <en>[Zdanie angielskie]</en>
* **Częste kolokacje:** <en>[Kolokacje]</en>

SCENARIUSZ B: Zdanie lub dłuższy tekst
### Tłumaczenie naturalne na angielski:
> <en>[Tłumaczenie angielskie]</en>
* **Znaczenie (PL):** [Tłumaczenie PL]
* **Mini-słowniczek:** <en>[Słowo 1]</en>, <en>[Słowo 2]</en>
* **Uwagi:** [Ton/gramatyka]

SCENARIUSZ C: Idiom lub przysłowie
### Angielski idiom / odpowiednik:
* **Znaczenie (PL):** [Tłumaczenie PL]
* **Przykład w zdaniu:** <en>[Zdanie angielskie]</en>
* **Kontekst (PL):** [Kontekst użycia]

SCENARIUSZ D: Rozmówki
### Przydatne zwroty: [Opis sytuacji]
* **<en>[Zdanie 1 EN]</en>** – [Tłumaczenie PL]
* **Mini-słowniczek:** <en>[Słowa kluczowe]</en>
* **Uwaga kulturowa:** [Wskazówka]

SCENARIUSZ E: Gramatyka (czasy, różnice, zasady)
### Zagadnienie gramatyczne: [Nazwa tematu]
* **Wyjaśnienie (PL):** [Wytłumaczenie reguły w języku polskim]
* **Budowa / Użycie:** [Przedstawienie struktury]
* **Przykłady obrazujące regułę:** 
  - <en>[Zdania EN]</en>
* **Tłumaczenie przykładów (PL):** [Polskie znaczenie]
* **Częste błędy / Uwagi:** [Na co uważać]

SCENARIUSZ F: Inne pytania językowe
### Swobodna odpowiedź eksperta:
* **Wyjaśnienie (PL):** [Naturalna odpowiedź eksperta]
* **Przydatne pojęcia:** <en>[Powiązane słówka]</en>"""

            user_prompt = f"Wejście użytkownika: \"{user_input}\"\nOdpowiedź:"

            raw_response, error = call_llm_api(system_prompt, user_prompt)

            if error:
                context['response'] = error
            else:
                clean_text = save_assistant_response(request, raw_response, user_input)
                context['response'] = make_text_clickable(clean_text)

    elif request.method == "GET":
        chat_id = request.GET.get('chat_id')
        if chat_id:
            old_chat = get_object_or_404(AssistantResponse, id=chat_id, user=request.user)
            context['response'] = make_text_clickable(old_chat.text)
            context['user_input'] = old_chat.user_input
    all_user_chats = AssistantResponse.objects.filter(user=request.user).order_by('-id')
    paginator = Paginator(all_user_chats, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context['all_user_chats'] = page_obj

    return render(request, 'ai/assistant.html', context)


def create_ai_word_list(request):
    context = {}
    if request.method == "POST":
        user_input = request.POST.get('prompt')
        if user_input:
            system_prompt = (
                "Jesteś automatem generującym dane. Nie pisz wstępów ani komentarzy. "
                "Format: Name:NazwaListy;Words:word1,word2,word3;\n"
                "Używaj tylko pojedynczych angielskich słów, bez opisów. "
                "Nazwa Listy (Name) MUSI zawierać spacje między słowami (np. 'My Trip To London')."
            )
            user_prompt = f"Stwórz listę angielskich słówek na temat: {user_input}."

            raw_response, error = call_llm_api(system_prompt, user_prompt)

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
                        messages.error(request,
                                       'AI wygenerowało słowa, których nie ma w naszej bazie lub AI nie zrozumiało pytania.')
                    else:
                        messages.success(request, 'Lista została utworzona.')
                        return redirect('word_list_detail', list_id=word_list.id)
                else:
                    messages.error(request, 'AI nie zachowało formatu. Spróbuj inaczej sformułować zapytanie.')

    return render(request, 'ai/input_query.html')