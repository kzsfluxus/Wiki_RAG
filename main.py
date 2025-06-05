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
from datetime import datetime
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'
import json
from pathlib import Path
from retriever import auto_fetch_from_config
from embedder import Embedder
from ollama_runner import run_mistral

WIKI_FILE = 'data/wiki_pages.json'
CONFIG_FILE = 'wiki_rag.conf'

def clear_cache():
    """Törli a cache-elt adatokat és indexeket"""
    try:
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
    except Exception as e:
        print(f"❌ Hiba cache törlése közben: {e}")
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
                    
    except Exception as e:
        print(f"⚠️ Nem sikerült ellenőrizni az adatok frissességét: {e}")
        return False
    
    return False

def load_docs():
    with open(WIKI_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_prompt(contexts, question):
    prompt = "Az alábbi MediaWiki oldalak alapján válaszolj a kérdésre:\n\n"
    for doc in contexts:
        prompt += f"== {doc['title']} ==\n{doc['text'][:1000]}\n\n"
    prompt += f"Kérdés: {question}\nVálasz:"
    return prompt

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
        
    except Exception as e:
        print(f"❌ Hiba az adatok betöltése közben: {e}")
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
            answer = run_mistral(prompt)
            print(f"\n💬 Válasz:\n{answer}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Kilépés...")
            break
        except Exception as e:
            print(f"❌ Hiba: {e}")

if __name__ == '__main__':
    main()