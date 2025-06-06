#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:31:49 2025
@author: zsolt
"""
import warnings
import os
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'
from flask import Flask, request, render_template
from pathlib import Path
from embedder import Embedder
from ollama_runner import run_ollama_model
from retriever import auto_fetch_from_config
from text_cleaner import clean_wiki_text
from prompt_builder import build_prompt
from docs_loader import clear_cache, should_refresh_data, load_docs, WIKI_FILE

app = Flask(__name__)

# Globális változók a cache-hez
_docs = None
_embedder = None
_last_config_check = 0

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
                    raw_answer = run_ollama_model(prompt)
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