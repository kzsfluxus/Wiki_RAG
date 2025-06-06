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
from pathlib import Path
from retriever import auto_fetch_from_config
from embedder import Embedder
from text_cleaner import clean_wiki_text
from ollama_runner import run_ollama_model
from prompt_builder import build_prompt
from docs_loader import clear_cache, should_refresh_data, load_docs, WIKI_FILE

def main():
    print("🚀 Wiki RAG rendszer indítása...")

    # Ellenőrizzük, hogy kell-e frissíteni az adatokat
    if should_refresh_data():
        print("🔄 Adatok frissítése...")
        clear_cache()
        auto_fetch_from_config()

        # Ellenőrizzük, hogy sikerült-e a letöltés
        if not Path(WIKI_FILE).exists():
            print("❌ Nem sikerült letölteni az adatokat!")
            return
    else:
        print("✅ Adatok naprakészek")

    # Adatok betöltése
    try:
        docs = load_docs()
        print(f"📚 Betöltve: {len(docs)} dokumentum")

        # Kiírjuk, hogy milyen oldalakat tartalmaz
        titles = [doc.get('title', 'Névtelen') for doc in docs]
        print(f"📄 Oldalak: {', '.join(titles)}")

    except Exception as error:
        print(f"❌ Hiba az adatok betöltése közben: {error}")
        return

    # Embedder inicializálása
    embedder = Embedder()

    # Index betöltése vagy építése
    if Path('data/index.faiss').exists() and not should_refresh_data():
        print("📊 Index betöltése...")
        embedder.load()
    else:
        print("🔨 Index építése...")
        embedder.build_index(docs)
        embedder.save()
        print("✅ Index mentve")

    print("\n🎯 RAG rendszer kész! Tedd fel a kérdéseidet.")
    print("(Üres válasz = kilépés)")

    # Fő ciklus
    while True:
        try:
            question = input("\n📌 Kérdés (üres = kilépés): ")
            if not question.strip():
                break

            print("🔍 Keresés...")
            results = embedder.query(question)

            print("🤖 Válasz generálása...")
            prompt = build_prompt(results, question)
            raw_answer = run_ollama_model(prompt)
            clean_answer = clean_wiki_text(raw_answer)
            print(f"\n💬 Válasz:\n{clean_answer}\n")

        except KeyboardInterrupt:
            print("\n👋 Kilépés...")
            break
        except Exception as error:
            print(f"❌ Hiba: {error}")

if __name__ == '__main__':
    main()
