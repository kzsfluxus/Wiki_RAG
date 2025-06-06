#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  6 14:20:01 2025

@author: zsolt
"""
import re

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