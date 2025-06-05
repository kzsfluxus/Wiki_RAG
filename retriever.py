#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:32:30 2025

@author: zsolt
"""

import mwclient
import json
from pathlib import Path

def fetch_wiki_pages(site_url, limit=3, path='/w/', output_path='data/documents.json', login_required=False):
    print(f"🌐 Csatlakozás: {site_url}{path}")
    site = mwclient.Site(site_url, path=path)
    
    if login_required:
        try:
            site.login('name', 'password')
            print("🔐 Sikeres bejelentkezés.")
        except Exception as e:
            print(f"❌ Bejelentkezési hiba: {e}")
            return

    pages = []
    
    for i, page in enumerate(site.allpages()):
        if i >= limit:
            break
        try:
            text = page.text()
            if text.strip():
                pages.append({'title': page.name, 'text': text})
                print(f"✅ Letöltve: {page.name}")
            else:
                print(f"⚠️ Üres oldal kihagyva: {page.name}")
        except Exception as e:
            print(f"⚠️ Skipping {page.name}: {e}")

    if not pages:
        print("❌ Nem sikerült letölteni egyetlen oldalt sem.")
        return

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)

    print(f"💾 Mentve: {output_path} ({len(pages)} oldal)")

def fetch_selected_pages(site_url, titles, path='/w/', output_path='data/documents.json'):
    site = mwclient.Site(site_url, path=path)
    pages = []
    for title in titles:
        try:
            page = site.pages[title]
            text = page.text()
            pages.append({'title': title, 'text': text})
            print(f"✅ Letöltve: {title}")
        except Exception as e:
            print(f"❌ Hiba {title} letöltésekor: {e}")

    if pages:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(pages, f, ensure_ascii=False, indent=2)

def fetch_related_pages(site_url, root_title, limit=50):
    site = mwclient.Site(site_url, path='/w/')
    data = site.api('query', list='prefixsearch', pssearch=root_title, pslimit=limit)
    results = data.get('query', {}).get('prefixsearch', [])
    titles = [res['title'] for res in results]
    fetch_selected_pages(site_url, titles)            
