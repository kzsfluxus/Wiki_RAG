#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:31:49 2025
@author: zsolt
"""
import warnings
import os
import shutil
import configparser
import re
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'
from flask import Flask, request, render_template
from pathlib import Path
import json
from embedder import Embedder
from ollama_runner import run_mistral
from retriever import auto_fetch_from_config

app = Flask(__name__)

WIKI_FILE = 'data/wiki_pages.json'
CONFIG_FILE = 'wiki_rag.conf'

# Globális változók a cache-hez
_docs = None
_embedder = None
_last_config_check = 0

def clear_cache():
    """Törli a cache-elt adatokat és indexeket"""
    global _docs, _embedder
    try:
        # Memória cache törlése
        _docs = None
        _embedder = None

        # Data könyvtár törlése
        if os.path.exists('data'):
            shutil.rmtree('data')
            print("🗑️ Cache törölve (data könyvtár)")

        # FAISS index törlése
        faiss_files = ['data/index.faiss', 'data/index.pkl']
        for file in faiss_files:
            if os.path.exists(file):
                os.remove(file)
                print(f"🗑️ Index fájl törölve: {file}")

        return True
    except Exception as error:
        print(f"❌ Hiba cache törlése közben: {error}")
        return False

def should_refresh_data():
    """Ellenőrzi, hogy szükséges-e az adatok frissítése"""
    # Ha nincs wiki fájl, frissíteni kell
    if not Path(WIKI_FILE).exists():
        print("ℹ️ Nincs wiki adat, letöltés szükséges")
        return True

    # Ha nincs config fájl, nem tudjuk ellenőrizni
    if not Path(CONFIG_FILE).exists():
        return False

    try:
        # Fájlok módosítási idejének ellenőrzése
        wiki_mtime = os.path.getmtime(WIKI_FILE)
        config_mtime = os.path.getmtime(CONFIG_FILE)

        # Ha a config újabb, mint a wiki adat, frissíteni kell
        if config_mtime > wiki_mtime:
            print("🔄 Konfiguráció újabb mint az adat, frissítés szükséges")
            return True

        # Ellenőrizzük, hogy a wiki fájlban tényleg a config szerinti város van-e
        with open(WIKI_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Config-ból olvassuk ki, hogy mit kellene tartalmaznia
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        if config.has_section('selected'):
            expected_pages = config.get('selected', 'pages', fallback='').strip()
            expected_titles = [p.strip() for p in expected_pages.split(',') if p.strip()]

            # Ellenőrizzük, hogy a várt oldalak szerepelnek-e
            actual_titles = [doc.get('title', '') for doc in data]

            for expected in expected_titles:
                if not any(expected.lower() in title.lower() for title in actual_titles):
                    print(f"⚠️ Hiányzó oldal az adatokból: {expected}")
                    return True

    except Exception as error:
        print(f"⚠️ Nem sikerült ellenőrizni az adatok frissességét: {error}")
        return False

    return False

def load_docs():
    global _docs
    if _docs is None:
        with open(WIKI_FILE, 'r', encoding='utf-8') as f:
            _docs = json.load(f)
        print(f"📚 Betöltve: {len(_docs)} dokumentum")
        titles = [doc.get('title', 'Névtelen') for doc in _docs]
        print(f"📄 Oldalak: {', '.join(titles)}")
    return _docs

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = Embedder()

        docs = load_docs()

        if Path('data/index.faiss').exists() and not should_refresh_data():
            print("📊 Index betöltése...")
            _embedder.load()
        else:
            print("🔨 Index építése...")
            _embedder.build_index(docs)
            _embedder.save()
            print("✅ Index mentve")

    return _embedder

def build_prompt(contexts, question):
    prompt = "Az alábbi MediaWiki oldalak alapján válaszolj a kérdésre:\n\n"
    for doc in contexts:
        prompt += f"== {doc['title']} ==\n{doc['text'][:1000]}\n\n"
    prompt += f"Kérdés: {question}\nVálasz:"
    return prompt

def initialize_system():
    """Rendszer inicializálása - ellenőrzi és frissíti az adatokat ha szükséges"""
    print("🚀 Wiki RAG Flask alkalmazás indítása...")

    # Ellenőrizzük, hogy kell-e frissíteni az adatokat
    if should_refresh_data():
        print("🔄 Adatok frissítése...")
        clear_cache()
        auto_fetch_from_config()

        # Ellenőrizzük, hogy sikerült-e a letöltés
        if not Path(WIKI_FILE).exists():
            print("❌ Nem sikerült letölteni az adatokat!")
            return False
    else:
        print("✅ Adatok naprakészek")

    # Előzetes betöltés
    try:
        load_docs()
        get_embedder()
        print("🎯 RAG rendszer kész!")
        return True
    except Exception as error:
        print(f"❌ Hiba az inicializálás során: {error}")
        return False

def clean_wiki_text(text):
    """
    Wikipedia szöveg teljes tisztítása a legtisztább válasz érdekében
    """
    if not text:
        return text

    # 1. Link formátumok tisztítása
    text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', text)  # [[link|display]] -> display
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)            # [[link]] -> link

    # 2. Template-ek eltávolítása
    text = re.sub(r'\{\{[^}]+\}\}', '', text)

    # 3. Referenciák eltávolítása
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^>]*\/>', '', text)

    # 4. HTML tagek eltávolítása
    text = re.sub(r'<[^>]+>', '', text)

    # 5. Wiki markup elemek
    text = re.sub(r"'''([^']+)'''", r'\1', text)  # '''bold''' -> bold
    text = re.sub(r"''([^']+)''", r'\1', text)    # ''italic'' -> italic

    # 6. Szóközök és sorok rendezése
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Több üres sor -> dupla
    text = re.sub(r' +', ' ', text)                 # Több szóköz -> egy
    text = re.sub(r'\n ', '\n', text)               # Sorok eleji szóközök

    return text.strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        # Rendszer inicializálása (csak az első kéréskor)
        if not hasattr(app, '_initialized'):
            if not initialize_system():
                return render_template('index.html', 
                                     question="", 
                                     clean_answer="❌ Hiba: Nem sikerült inicializálni a rendszert",
                                     error=True)
            app._initialized = True

        # Változók inicializálása
        question = ""
        clean_answer = ""  # Ez fontos!

        if request.method == 'POST':
            question = request.form.get('question', '').strip()
            if question:
                try:
                    print(f"🔍 Kérdés: {question}")
                    embedder = get_embedder()
                    results = embedder.query(question)
                    print("🤖 Válasz generálása...")
                    prompt = build_prompt(results, question)
                    raw_answer = run_mistral(prompt)
                    clean_answer = clean_wiki_text(raw_answer)  # Itt használod a tisztító függvényt
                    print(f"✅ Tisztított válasz: {clean_answer[:100]}...")  # Debug log
                except Exception as error:
                    print(f"❌ Hiba a kérdés feldolgozása során: {error}")
                    clean_answer = f"❌ Hiba történt: {str(error)}"
            else:
                clean_answer = "Kérlek, adj meg egy kérdést!"

        return render_template('index.html', question=question, clean_answer=clean_answer)

    except Exception as error:
        print(f"❌ Általános hiba: {error}")
        return render_template('index.html', 
                             question="", 
                             clean_answer=f"❌ Rendszerhiba: {str(error)}",
                             error=True)

@app.route('/refresh', methods=['POST'])
def refresh_data():
    """Manuális adatfrissítés végpont"""
    try:
        print("🔄 Manuális cache törlés...")
        clear_cache()
        auto_fetch_from_config()

        # Rendszer újrainicializálása
        if hasattr(app, '_initialized'):
            delattr(app, '_initialized')

        return {"status": "success", "message": "Adatok frissítve!"}
    except Exception as error:
        return {"status": "error", "message": f"Hiba: {str(error)}"}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)