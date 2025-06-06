#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  6 22:38:55 2025

@author: zsolt
"""

import os
import json
from pathlib import Path
import shutil
import configparser

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
    with open(WIKI_FILE, 'r', encoding='utf-8') as file:
        return json.load(file)
