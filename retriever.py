#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:31:49 2025
@author: zsolt
"""

import mwclient
import os
import json
from pathlib import Path
import configparser

CONFIG_PATH = 'wiki_rag.conf'
DEFAULT_OUTPUT = 'data/wiki_pages.json'

def load_config(path=CONFIG_PATH):
    config = configparser.ConfigParser()
    config.read(path)
    return config

def save_pages(pages, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(pages, file, ensure_ascii=False, indent=2)
    print(f"✅ Letöltve: {len(pages)} oldal --> {output_path}")

def connect(site_url, path, username=None, password=None):
    print(f"🔗 Csatlakozás: https://{site_url}{path}")
    site = mwclient.Site(site_url, path=path)
    if username and password:
        site.login(username, password)
        print("🔐 Bejelentkezés sikeres")
    return site

def fetch_wiki_pages(site_url, path='/wiki/', username=None, password=None, limit=50, output_path=DEFAULT_OUTPUT):
    site = connect(site_url, path, username, password)
    pages = []
    for i, page in enumerate(site.allpages()):
        if i >= limit:
            break
        try:
            text = page.text()
            pages.append({'title': page.name, 'text': text})
        except Exception as error:
            print(f"❌ Skipping {page.name}: {error}")
    save_pages(pages, output_path)

def fetch_selected_pages(site_url, titles, path='/w/', username=None, password=None):
    site = mwclient.Site(site_url, path=path)
    if username and password:
        site.login(username, password)
        print("🔐 Bejelentkezés sikeres")

    pages = []
    print(f"🔗 Csatlakozás: https://{site_url}{path}")
    print(f"📄 Letöltendő oldalak: {titles}")

    for title in titles:
        try:
            print(f"🔄 Letöltés: {title}")
            page = site.pages[title]

            # Ellenőrizzük, hogy létezik-e az oldal
            if not page.exists:
                print(f"⚠️ Az oldal nem létezik: {title}")
                continue

            text = page.text()
            if text.strip():  # Ellenőrizzük, hogy van-e tartalom
                pages.append({
                    'title': title,
                    'text': text
                })
                print(f"✅ Sikeresen letöltve: {title} ({len(text)} karakter)")
            else:
                print(f"⚠️ Üres oldal: {title}")
        except Exception as error:
            print(f"❌ Hiba '{title}' letöltése közben: {error}")

    # Mentés és eredmény kiírása
    if pages:
        os.makedirs(os.path.dirname(DEFAULT_OUTPUT), exist_ok=True)
        with open(DEFAULT_OUTPUT, 'w', encoding='utf-8') as file:
            json.dump(pages, file, ensure_ascii=False, indent=2)
        print(f"✅ Összesen letöltve: {len(pages)} oldal --> {DEFAULT_OUTPUT}")
    else:
        print("❌ Nem sikerült egyetlen oldalt sem letölteni.")

def fetch_related_pages(site_url, root_title, limit=50, path='/w/', username=None, password=None):
    site = mwclient.Site(site_url, path=path)
    if username and password:
        site.login(username, password)
        print("🔐 Bejelentkezés sikeres")

    print(f"🔗 Csatlakozás: https://{site_url}{path}")
    print(f"🔍 Keresés: '{root_title}' kezdetű oldalak")

    try:
        results = site.api('query', list='prefixsearch', pssearch=root_title, pslimit=limit)
        titles = [res['title'] for res in results.get('query', {}).get('prefixsearch', [])]

        if not titles:
            print(f"⚠️ Nincs találat: '{root_title}' kezdetű oldalakra.")
            return

        print(f"🔹 Talált oldalak ({len(titles)}): {titles}")
        fetch_selected_pages(site_url, titles, path=path, username=username, password=password)

    except Exception as error:
        print(f"❌ Hiba prefixsearch közben: {error}")

def fetch_selected_pages_return(site_url, titles, path='/w/', username=None, password=None):
    """
    Kiválasztott oldalak letöltése és visszaadása (mentés nélkül)
    """
    site = mwclient.Site(site_url, path=path)
    if username and password:
        site.login(username, password)
        print("🔐 Bejelentkezés sikeres")

    pages = []
    print(f"🔗 Csatlakozás: https://{site_url}{path}")
    print(f"📄 Letöltendő oldalak: {titles}")

    for title in titles:
        try:
            print(f"🔄 Letöltés: {title}")
            page = site.pages[title]

            if not page.exists:
                print(f"⚠️ Az oldal nem létezik: {title}")
                continue

            text = page.text()
            if text.strip():
                pages.append({
                    'title': title,
                    'text': text
                })
                print(f"✅ Sikeresen letöltve: {title} ({len(text)} karakter)")
            else:
                print(f"⚠️ Üres oldal: {title}")
        except Exception as error:
            print(f"❌ Hiba '{title}' letöltése közben: {error}")

    return pages

def fetch_related_pages_return(site_url, root_title, limit=50, path='/w/', username=None, password=None):
    """
    Kapcsolódó oldalak letöltése és visszaadása (mentés nélkül)
    """
    site = mwclient.Site(site_url, path=path)
    if username and password:
        site.login(username, password)
        print("🔐 Bejelentkezés sikeres")

    print(f"🔗 Csatlakozás: https://{site_url}{path}")
    print(f"🔍 Keresés: '{root_title}' kezdetű oldalak")

    try:
        results = site.api('query', list='prefixsearch', pssearch=root_title, pslimit=limit)
        titles = [res['title'] for res in results.get('query', {}).get('prefixsearch', [])]

        if not titles:
            print(f"⚠️ Nincs találat: '{root_title}' kezdetű oldalakra.")
            return []

        print(f"🔹 Talált oldalak ({len(titles)}): {titles}")
        return fetch_selected_pages_return(site_url, titles, path=path, username=username, password=password)

    except Exception as error:
        print(f"❌ Hiba prefixsearch közben: {error}")
        return []

def auto_fetch_from_config(conf_file='wiki_rag.conf'):
    config = configparser.ConfigParser()

    if not os.path.exists(conf_file):
        print(f"❌ Konfigurációs fájl nem található: {conf_file}")
        return

    config.read(conf_file)

    if not config.has_section('wiki') or not config.get('wiki', 'url', fallback='').strip():
        print("❌ A 'wiki' szekció vagy az 'url' hiányzik a konfigurációból.")
        return

    site_url = config.get('wiki', 'url').strip()
    path = config.get('wiki', 'path', fallback='/w/').strip()
    username = config.get('wiki', 'username', fallback=None)
    password = config.get('wiki', 'password', fallback=None)

    print(f"📋 Konfig betöltve: {site_url}")

    # selected pages
    selected = config.get('selected', 'pages', fallback='').strip() if config.has_section('selected') else ''
    selected_pages = [p.strip() for p in selected.split(',') if p.strip()]

    # related pages
    related_root = config.get('related', 'root', fallback='').strip() if config.has_section('related') else ''
    related_limit_str = config.get('related', 'limit', fallback='50').strip() if config.has_section('related') else '50'
    related_limit = int(related_limit_str) if related_limit_str.isdigit() else 50

    all_pages = []  # Közös lista az összes oldal számára

    if selected_pages:
        print(f"📝 Kiválasztott oldalak letöltése: {selected_pages}")
        selected_data = fetch_selected_pages_return(site_url, selected_pages, path=path, username=username, password=password)
        all_pages.extend(selected_data)

    if related_root:  # Változás: elif helyett if
        print(f"🔗 Kapcsolódó oldalak letöltése: '{related_root}' gyök alapján")
        related_data = fetch_related_pages_return(site_url, related_root, limit=related_limit, path=path, username=username, password=password)
        all_pages.extend(related_data)

    if not selected_pages and not related_root:
        print("⚠️ Nincs megadva letöltendő oldal a [selected] vagy [related] szekcióban.")
        return

    # Végső mentés
    if all_pages:
        os.makedirs(os.path.dirname(DEFAULT_OUTPUT), exist_ok=True)
        with open(DEFAULT_OUTPUT, 'w', encoding='utf-8') as file:
            json.dump(all_pages, file, ensure_ascii=False, indent=2)
        print(f"✅ Összesen letöltve: {len(all_pages)} oldal --> {DEFAULT_OUTPUT}")
    else:
        print("❌ Nem sikerült egyetlen oldalt sem letölteni.")

# Példa használat
if __name__ == "__main__":
    auto_fetch_from_config()