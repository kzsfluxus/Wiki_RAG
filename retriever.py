#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:31:49 2025
@author: zsolt

MediaWiki oldalak letöltésére szolgáló modul.

Ez a modul MediaWiki alapú wiki oldalak letöltésére szolgál különböző módszerekkel:
- Összes oldal letöltése limit-tel
- Kiválasztott oldalak letöltése
- Kapcsolódó oldalak keresése prefix alapján
- Konfigurációs fájl alapú automatikus letöltés
"""

import os
import json
from pathlib import Path
import configparser
import logging
import mwclient

logger = logging.getLogger(__name__)

CONFIG_PATH = Path('wiki_rag.ini')
DEFAULT_OUTPUT = Path('data/wiki_pages.json')
MAX_DOWNLOAD = 100  # Maximálisan letölthető oldalak száma konstans


def load_config(path=CONFIG_PATH):
    """
    Konfigurációs fájl betöltése.

    Args:
        path (Path, optional): A konfigurációs fájl útvonala.
            Alapértelmezett: CONFIG_PATH

    Returns:
        configparser.ConfigParser: A betöltött konfiguráció objektum.
    """
    config = configparser.ConfigParser()
    config.read(path)
    return config


def _parse_selected_pages(config):
    """
    Feldolgozza a [selected] szekció pages beállításait.
    
    Args:
        config (configparser.ConfigParser): A konfiguráció objektum
        
    Returns:
        list: A kiválasztott oldalak listája
        
    Raises:
        ValueError: Ha keveredik a pages és pages.N formátum
    """
    if not config.has_section('selected'):
        return []
    
    pages = []
    has_simple_pages = False
    has_numbered_pages = False
    
    # Ellenőrizzük a simple pages formátumot
    simple_pages = config.get('selected', 'pages', fallback='').strip()
    if simple_pages:
        has_simple_pages = True
        pages.extend([p.strip() for p in simple_pages.split(',') if p.strip()])
    
    # Ellenőrizzük a numbered pages formátumot (pages.1, pages.2, stb.)
    for key in config.options('selected'):
        if key.startswith('pages.') and key[6:].isdigit():
            has_numbered_pages = True
            numbered_pages = config.get('selected', key, fallback='').strip()
            if numbered_pages:
                pages.extend([p.strip() for p in numbered_pages.split(',') if p.strip()])
    
    # Ellenőrizzük, hogy keveredik-e a két formátum
    if has_simple_pages and has_numbered_pages:
        raise ValueError("Hiba: A 'pages' és 'pages.N' formátumok nem keveredhetnek az ini fájlban!")
    
    return pages


def save_pages(pages, output_path):
    """
    Wiki oldalak mentése JSON fájlba.

    Args:
        pages (list): A mentendő wiki oldalak listája (dict-ek 'title' és 'text' kulcsokkal).
        output_path (str vagy Path): A kimeneti fájl útvonala.

    Raises:
        OSError: Ha a könyvtár létrehozása vagy a fájl írása nem sikerül.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(pages, file, ensure_ascii=False, indent=2)
    logger.info("Letöltve: %d oldal --> %s", len(pages), output_path)


def connect(site_url, path, username=None, password=None):
    """
    Kapcsolódás MediaWiki site-hoz.

    Args:
        site_url (str): A wiki site URL-je (pl. 'hu.wikipedia.org').
        path (str): A wiki útvonal (pl. '/w/').
        username (str, optional): Felhasználónév bejelentkezéshez.
        password (str, optional): Jelszó bejelentkezéshez.

    Returns:
        mwclient.Site: A MediaWiki site objektum.

    Raises:
        mwclient.errors.LoginError: Ha a bejelentkezés sikertelen.
    """
    logger.info("Csatlakozás: https://%s%s", site_url, path)
    site = mwclient.Site(site_url, path=path)
    if username and password:
        site.login(username, password)
        logger.info("Bejelentkezés sikeres")
    return site


def fetch_wiki_pages(site_url, path='/wiki/', username=None,
                     password=None, limit=50, output_path=DEFAULT_OUTPUT):
    """
    Wiki oldalak letöltése az összes oldal listájából.

    Args:
        site_url (str): A wiki site URL-je.
        path (str, optional): A wiki útvonal. Alapértelmezett: '/wiki/'
        username (str, optional): Felhasználónév bejelentkezéshez.
        password (str, optional): Jelszó bejelentkezéshez.
        limit (int, optional): Letöltendő oldalak száma. Alapértelmezett: 50
        output_path (Path, optional): Kimeneti fájl útvonala.
            Alapértelmezett: DEFAULT_OUTPUT

    Raises:
        Exception: Ha a wiki kapcsolat vagy letöltés sikertelen.
    """
    site = connect(site_url, path, username, password)
    pages = []
    logger.info("Wiki oldalak letöltése kezdődik - limit: %d", limit)

    for i, page in enumerate(site.allpages()):
        if i >= limit:
            break
        try:
            text = page.text()
            pages.append({'title': page.name, 'text': text})
            logger.debug(
                "Oldal letöltve: %s (%d karakter)",
                page.name,
                len(text))
        except Exception as error:
            logger.warning("Oldal kihagyva %s: %s", page.name, error)

    save_pages(pages, output_path)


def fetch_selected_pages(site_url, titles, path='/w/',
                         username=None, password=None):
    """
    Kiválasztott wiki oldalak letöltése címek alapján.

    Args:
        site_url (str): A wiki site URL-je.
        titles (list): A letöltendő oldalak címeinek listája.
        path (str, optional): A wiki útvonal. Alapértelmezett: '/w/'
        username (str, optional): Felhasználónév bejelentkezéshez.
        password (str, optional): Jelszó bejelentkezéshez.

    Note:
        Az oldalak a DEFAULT_OUTPUT útvonalra kerülnek mentésre.
        Hiányzó vagy üres oldalak logolva lesznek, de nem törlik meg a folyamatot.
    """
    site = mwclient.Site(site_url, path=path)
    if username and password:
        site.login(username, password)
        logger.info("Bejelentkezés sikeres")

    pages = []
    logger.info("Csatlakozás: https://%s%s", site_url, path)
    logger.info("Letöltendő oldalak: %s", titles)

    for title in titles:
        try:
            logger.debug("Letöltés: %s", title)
            page = site.pages[title]

            # Ellenőrizzük, hogy létezik-e az oldal
            if not page.exists:
                logger.warning("Az oldal nem létezik: %s", title)
                continue

            text = page.text()
            if text.strip():  # Ellenőrizzük, hogy van-e tartalom
                pages.append({
                    'title': title,
                    'text': text
                })
                logger.info(
                    "Sikeresen letöltve: %s (%d karakter)",
                    title,
                    len(text))
            else:
                logger.warning("Üres oldal: %s", title)
        except Exception as error:
            logger.error("Hiba '%s' letöltése közben: %s", title, error)

    # Mentés és eredmény kiírása
    if pages:
        os.makedirs(os.path.dirname(DEFAULT_OUTPUT), exist_ok=True)
        with open(DEFAULT_OUTPUT, 'w', encoding='utf-8') as file:
            json.dump(pages, file, ensure_ascii=False, indent=2)
        logger.info(
            "Összesen letöltve: %d oldal --> %s",
            len(pages),
            DEFAULT_OUTPUT)
    else:
        logger.error("Nem sikerült egyetlen oldalt sem letölteni.")


def fetch_related_pages(site_url, root_title, limit=50,
                        path='/w/', username=None, password=None):
    """
    Kapcsolódó oldalak letöltése prefix keresés alapján.

    Args:
        site_url (str): A wiki site URL-je.
        root_title (str): A keresési prefix (pl. "Python" minden Python-nal kezdődő oldalhoz).
        limit (int, optional): Maximum találatok száma. Alapértelmezett: 50
        path (str, optional): A wiki útvonal. Alapértelmezett: '/w/'
        username (str, optional): Felhasználónév bejelentkezéshez.
        password (str, optional): Jelszó bejelentkezéshez.

    Note:
        A talált oldalak a fetch_selected_pages függvényen keresztül töltődnek le.
    """
    site = mwclient.Site(site_url, path=path)
    if username and password:
        site.login(username, password)
        logger.info("Bejelentkezés sikeres")

    logger.info("Csatlakozás: https://%s%s", site_url, path)
    logger.info("Keresés: '%s' kezdetű oldalak", root_title)

    try:
        results = site.api(
            'query',
            list='prefixsearch',
            pssearch=root_title,
            pslimit=limit)
        titles = [
            res['title'] for res in results.get(
                'query', {}).get(
                'prefixsearch', [])]

        if not titles:
            logger.warning(
                "Nincs találat: '%s' kezdetű oldalakra.",
                root_title)
            return

        logger.info("Talált oldalak (%d): %s", len(titles), titles)
        fetch_selected_pages(
            site_url,
            titles,
            path=path,
            username=username,
            password=password)

    except Exception as error:
        logger.error("Hiba prefixsearch közben: %s", error)


def fetch_selected_pages_return(
        site_url, titles, path='/w/', username=None, password=None):
    """
    Kiválasztott oldalak letöltése és visszaadása (mentés nélkül).

    Args:
        site_url (str): A wiki site URL-je.
        titles (list): A letöltendő oldalak címeinek listája.
        path (str, optional): A wiki útvonal. Alapértelmezett: '/w/'
        username (str, optional): Felhasználónév bejelentkezéshez.
        password (str, optional): Jelszó bejelentkezéshez.

    Returns:
        list: A letöltött oldalak listája (dict-ek 'title' és 'text' kulcsokkal).

    Note:
        Ez a függvény nem ment fájlba, csak visszaadja az adatokat.
        Hiányzó vagy üres oldalak kihagyásra kerülnek.
    """
    site = mwclient.Site(site_url, path=path)
    if username and password:
        site.login(username, password)
        logger.info("Bejelentkezés sikeres")

    pages = []
    logger.info("Csatlakozás: https://%s%s", site_url, path)
    logger.info("Letöltendő oldalak: %s", titles)

    for title in titles:
        try:
            logger.debug("Letöltés: %s", title)
            page = site.pages[title]

            if not page.exists:
                logger.warning("Az oldal nem létezik: %s", title)
                continue

            text = page.text()
            if text.strip():
                pages.append({
                    'title': title,
                    'text': text
                })
                logger.info(
                    "Sikeresen letöltve: %s (%d karakter)",
                    title,
                    len(text))
            else:
                logger.warning("Üres oldal: %s", title)
        except Exception as error:
            logger.error("Hiba '%s' letöltése közben: %s", title, error)

    return pages


def fetch_related_pages_return(
        site_url, root_title, limit=50, path='/w/', username=None, password=None):
    """
    Kapcsolódó oldalak letöltése és visszaadása (mentés nélkül).

    Args:
        site_url (root_title (str): A keresési prefix.
        limit (int, optional): Maximum találatok száma. Alapértelmezett: 50
        path (str, optional): A wiki útvonal. Alapértelmezett: '/w/'
        username (str, optional): Felhasználónév bejelentkezéshez.
        password (str, optional): Jelszó bejelentkezéshez.

    Returns:
        list: A letöltött kapcsolódó oldalak listája, üres lista hiba esetén.

    Note:
        Ez a függvény nem ment fájlba, csak visszaadja az adatokat.
        Prefix keresést használ a MediaWiki API-n keresztül.
    """
    site = mwclient.Site(site_url, path=path)
    if username and password:
        site.login(username, password)
        logger.info("Bejelentkezés sikeres")

    logger.info("Csatlakozás: https://%s%s", site_url, path)
    logger.info("Keresés: '%s' kezdetű oldalak", root_title)

    try:
        results = site.api(
            'query',
            list='prefixsearch',
            pssearch=root_title,
            pslimit=limit)
        titles = [
            res['title'] for res in results.get(
                'query', {}).get(
                'prefixsearch', [])]

        if not titles:
            logger.warning(
                "Nincs találat: '%s' kezdetű oldalakra.",
                root_title)
            return []

        logger.info("Talált oldalak (%d): %s", len(titles), titles)
        return fetch_selected_pages_return(
            site_url, titles, path=path, username=username, password=password)

    except Exception as error:
        logger.error("Hiba prefixsearch közben: %s", error)
        return []


def auto_fetch_from_config(conf_file='wiki_rag.ini'):
    """
    Automatikus wiki oldalak letöltése konfigurációs fájl alapján.

    Ez a függvény beolvassa a konfigurációs fájlt és a benne megadott
    beállítások alapján letölti a wiki oldalakat. Az új logika szerint:
    
    1. Ha a [selected] és [related] szekciók üresek, a [wiki] url-éből tölt le.
    2. Ha nincs limit megadva a [wiki] szekcióban, a MAX_DOWNLOAD konstans lép érvénybe.
    3. Az összes letöltendő oldal nem haladhatja meg a limitet.
    4. Ha keveredik a pages és pages.N formátum, figyelmeztető üzenettel kilép.

    Args:
        conf_file (str, optional): A konfigurációs fájl neve/útvonala.
            Alapértelmezett: 'wiki_rag.ini'

    Returns:
        None

    Note:
        A konfigurációs fájlnak a következő szekciókat tartalmazhatja:
        - [wiki]: url, path, username, password, limit
        - [selected]: pages vagy pages.1, pages.2, stb.
        - [related]: root, limit

    Raises:
        Exception: Ha kritikus hiba történik a letöltés során (logolva).
    """
    config = configparser.ConfigParser()

    if not os.path.exists(conf_file):
        logger.error("Konfigurációs fájl nem található: %s", conf_file)
        return

    config.read(conf_file)

    if not config.has_section('wiki') or not config.get(
            'wiki', 'url', fallback='').strip():
        logger.error(
            "A 'wiki' szekció vagy az 'url' hiányzik a konfigurációból.")
        return

    site_url = config.get('wiki', 'url').strip()
    path = config.get('wiki', 'path', fallback='/w/').strip()
    username = config.get('wiki', 'username', fallback=None)
    password = config.get('wiki', 'password', fallback=None)
    
    # Limit ellenőrzése a [wiki] szekcióban
    wiki_limit_str = config.get('wiki', 'limit', fallback='').strip()
    if wiki_limit_str and wiki_limit_str.isdigit():
        max_total_limit = int(wiki_limit_str)
    else:
        max_total_limit = MAX_DOWNLOAD
        logger.info("Nincs megadva limit a [wiki] szekcióban, használjuk a MAX_DOWNLOAD = %d konstanst", MAX_DOWNLOAD)

    logger.info("Konfig betöltve: %s, maximális limit: %d", site_url, max_total_limit)

    try:
        # selected pages feldolgozása
        selected_pages = _parse_selected_pages(config)
    except ValueError as e:
        logger.error(str(e))
        return

    # related pages
    related_root = config.get('related', 'root', fallback='').strip(
    ) if config.has_section('related') else ''
    related_limit_str = config.get('related', 'limit', fallback='50').strip(
    ) if config.has_section('related') else '50'
    related_limit = int(
        related_limit_str) if related_limit_str.isdigit() else 50

    all_pages = []  # Közös lista az összes oldal számára
    total_pages_count = 0

    # 1. eset: Ha mind a [selected] és [related] üres, akkor a wiki url-ét töltjük le
    if not selected_pages and not related_root:
        logger.info("Sem [selected], sem [related] szekció nincs megadva, letöltjük a wiki url-t a limitig")
        fetch_wiki_pages(
            site_url, 
            path=path, 
            username=username, 
            password=password, 
            limit=max_total_limit, 
            output_path=DEFAULT_OUTPUT
        )
        return

    # 2. eset: selected pages feldolgozása
    if selected_pages:
        # Ellenőrizzük, hogy nem lépjük-e túl a limitet
        if len(selected_pages) > max_total_limit:
            logger.warning("A kiválasztott oldalak száma (%d) meghaladja a limitet (%d), csak az első %d oldalt töltjük le", 
                         len(selected_pages), max_total_limit, max_total_limit)
            selected_pages = selected_pages[:max_total_limit]
        
        logger.info("Kiválasztott oldalak letöltése: %s", selected_pages)
        selected_data = fetch_selected_pages_return(
            site_url, selected_pages, path=path, username=username, password=password)
        all_pages.extend(selected_data)
        total_pages_count += len(selected_data)

    # 3. eset: related pages feldolgozása (ha még van hely a limitben)
    if related_root and total_pages_count < max_total_limit:
        remaining_limit = max_total_limit - total_pages_count
        actual_related_limit = min(related_limit, remaining_limit)
        
        logger.info(
            "Kapcsolódó oldalak letöltése: '%s' gyök alapján, limit: %d (maradék hely: %d)",
            related_root, actual_related_limit, remaining_limit)
        
        related_data = fetch_related_pages_return(
            site_url,
            related_root,
            limit=actual_related_limit,
            path=path,
            username=username,
            password=password)
        all_pages.extend(related_data)
        total_pages_count += len(related_data)
    elif related_root and total_pages_count >= max_total_limit:
        logger.warning("A limit (%d) már elérve a selected oldalakkal, related oldalakat nem töltjük le", max_total_limit)

    # Végleges ellenőrzés és mentés
    if total_pages_count > max_total_limit:
        logger.warning("A letöltött oldalak száma (%d) meghaladja a limitet (%d), csak az első %d oldalt mentjük", 
                     total_pages_count, max_total_limit, max_total_limit)
        all_pages = all_pages[:max_total_limit]

    # Végső mentés
    if all_pages:
        os.makedirs(os.path.dirname(DEFAULT_OUTPUT), exist_ok=True)
        with open(DEFAULT_OUTPUT, 'w', encoding='utf-8') as file:
            json.dump(all_pages, file, ensure_ascii=False, indent=2)
        logger.info(
            "Összesen letöltve: %d oldal --> %s",
            len(all_pages),
            DEFAULT_OUTPUT)
    else:
        logger.error("Nem sikerült egyetlen oldalt sem letölteni.")


# Példa használat
if __name__ == "__main__":
    # Logging beállítása csak a fő fájlban
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    auto_fetch_from_config()