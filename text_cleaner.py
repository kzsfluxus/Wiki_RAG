#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  6 14:20:01 2025
@author: zsolt

Ez a modul a Wikipedia szövegek előfeldolgozását és tisztítását végzi, hogy azok 
alkalmasak legyenek további feldolgozásra (pl. gépi tanulás, keresés, elemzés).
A főbb funkciók:
- Wiki markup, HTML tagek, speciális karakterek és felesleges whitespace-ek eltávolítása
- Szövegek egységesítése és normalizálása
- Különféle testreszabható tisztítási lépések implementálása

A modul használatával biztosítható, hogy a bemeneti Wikipedia szövegek egységes, 
tiszta formában kerüljenek további feldolgozásra.
"""
import re


def clean_wiki_text(text) -> str:
    """
    Tisztítja a bemeneti Wikipedia szöveget előfeldolgozás céljából.

    A függvény elvégzi:
    - HTML tagek, speciális karakterek, felesleges whitespace-ek eltávolítását
    - Sorvégi szóközök és üres sorok törlését
    - Többszörös szóközök egy szóközre cserélését
    - Hivatkozások, források, sablonok vagy egyéb wiki markup eltávolítását (pl. [[link]], {{címke}})
    - Egyéb, projekt-specifikus tisztításokat

    Példák:
        >>> clean_wiki_text("Ez egy példa <b>HTML</b> taggel.")
        'Ez egy példa HTML taggel.'
        >>> clean_wiki_text("Ez egy [[Belso link]] teszt.")
        'Ez egy teszt.'

    Args:
        text (str): Bemeneti, tisztítandó Wikipedia szöveg.

    Returns:
        str: Tisztított szöveg.
    """
    if not text:
        return text

    # 1. Link formátumok tisztítása
    text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2',
                  text)  # [[link|display]] -> display
    text = re.sub(
        r'\[\[([^\]]+)\]\]',
        r'\1',
        text)            # [[link]] -> link

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
