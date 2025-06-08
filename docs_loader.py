#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  6 22:38:55 2025
@author: zsolt

A docs_loader modul felelős a dokumentációs adatok kezeléséért, betöltéséért 
és a gyorsítótár (cache) műveleteiért.

Főbb funkciók:
- Dokumentációs gyorsítótár törlése.
- Annak eldöntése, hogy szükséges-e az adatok frissítése.
- Dokumentációs adatok betöltése tárolt fájlból.

A modul segíti a dokumentáció naprakészen tartását, valamint optimalizálja az 
adatbetöltést cache használatával.
"""
import os
import json
from pathlib import Path
import shutil
import configparser
import logging

logger = logging.getLogger(__name__)

WIKI_FILE = Path('data/wiki_pages.json')
CONFIG_FILE = Path('wiki_rag.conf')


def clear_cache():
    """
    Törli a dokumentációs gyorsítótárat.

    Returns:
        None
    """
    try:
        data_dir = Path('data')

        # Ha létezik a data könyvtár, töröljük az egészet
        if data_dir.exists():
            shutil.rmtree(data_dir)
            logger.info("Cache törölve (data könyvtár)")

        logger.info("Cache sikeresen törölve")
        return True
    except Exception as error:
        logger.error("Hiba cache törlése közben: %s", error)
        return False


def should_refresh_data() -> bool:
    """
    Eldönti, hogy frissíteni kell-e az adatokat az utolsó betöltés alapján.
    
    Returns:
        bool: Igaz, ha frissíteni kell, egyébként hamis.
   """
    # Ha nincs wiki fájl, frissíteni kell
    if not Path(WIKI_FILE).exists():
        logger.info("Nincs wiki adat, letöltés szükséges")
        return True

    # Ha nincs config fájl, nem tudjuk ellenőrizni
    if not Path(CONFIG_FILE).exists():
        logger.debug(
            "Nincs config fájl, nem ellenőrizhető a frissítés szükségessége")
        return False

    try:
        # Fájlok módosítási idejének ellenőrzése
        wiki_mtime = os.path.getmtime(WIKI_FILE)
        config_mtime = os.path.getmtime(CONFIG_FILE)

        # Ha a config újabb, mint a wiki adat, frissíteni kell
        if config_mtime > wiki_mtime:
            logger.info("Konfiguráció újabb mint az adat, frissítés szükséges")
            return True

        # Ellenőrizzük, hogy a wiki fájlban tényleg a config szerinti város
        # van-e
        with open(WIKI_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Config-ból olvassuk ki, hogy mit kellene tartalmaznia
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        if config.has_section('selected'):
            expected_pages = config.get(
                'selected', 'pages', fallback='').strip()
            expected_titles = [p.strip()
                               for p in expected_pages.split(',') if p.strip()]

            # Ellenőrizzük, hogy a várt oldalak szerepelnek-e
            actual_titles = [doc.get('title', '') for doc in data]
            for expected in expected_titles:
                if not any(expected.lower() in title.lower()
                           for title in actual_titles):
                    logger.warning("Hiányzó oldal az adatokból: %s", expected)
                    return True

        logger.debug("Adatok frissítése nem szükséges")

    except Exception as error:
        logger.warning(
            "Nem sikerült ellenőrizni az adatok frissességét: %s",
            error)
        return False

    return False


def load_docs() -> dict:
    """
    Betölti a dokumentációs adatokat a megadott útvonalról.

    Returns:
        dict: A betöltött dokumentációs adatok.
    """
    try:
        with open(WIKI_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
        logger.debug(
            "Wiki dokumentumok sikeresen betöltve: %d dokumentum",
            len(data))
        return data
    except Exception as error:
        logger.error("Hiba wiki dokumentumok betöltése közben: %s", error)
        raise
