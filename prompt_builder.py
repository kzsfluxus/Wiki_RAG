#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  6 22:33:15 2025
@author: zsolt

Prompt építő modul MediaWiki alapú kérdés-válasz rendszerhez.
"""


def build_prompt(contexts, question):
    """
    Prompt szöveg készítése MediaWiki kontextusok és kérdés alapján.

    Ez a függvény egy strukturált prompt-ot épít fel, amely tartalmazza
    a releváns MediaWiki oldalak tartalmát és a felhasználó kérdését.
    A prompt célja, hogy egy AI modell részletes választ tudjon adni
    a wiki tartalmak alapján.

    Args:
        contexts (list): MediaWiki dokumentumok listája. Minden elem egy dict,
            amely 'title' és 'text' kulcsokat tartalmaz.
        question (str): A felhasználó kérdése, amire választ kell adni.

    Returns:
        str: A felépített prompt szöveg, amely tartalmazza a wiki forrásokat,
            a kérdést és az instrukciót a válaszadáshoz.

    Examples:
        >>> contexts = [{'title': 'Python', 'text': 'Python egy programozási nyelv...'}]
        >>> question = "Mi a Python?"
        >>> prompt = build_prompt(contexts, question)
        >>> print(prompt)
        Az alábbi MediaWiki oldalak alapján adj részletes választ a kérdésre...

    Note:
        Ha nincs kontextus megadva, a függvény egy alapértelmezett üzenetet
        ad vissza, amely jelzi, hogy nincs releváns információ.
        A wiki szövegek maximum 1200 karakterre vannak levágva.
    """
    if not contexts:
        return f"Kérdés: {question}\n\nVálasz: Sajnos nincs releváns információ a dokumentumokban."

    prompt = "Az alábbi MediaWiki-oldalak alapján válaszolj a kérdésre **helyes és természetes magyar nyelven**.\n"
    prompt += "A válasz legyen részletes, tényszerű és jól megfogalmazott, ügyelve az alany–állítmány egyeztetésre, "
    prompt += "helyesírásra és nyelvtani pontosságra.\n"
    prompt += "Elsősorban a wiki tartalmakat használd, de ha szükséges, egészítsd ki általános tudással is.\n\n"
    prompt += "## FORRÁSOK:\n\n"
    
    for i, doc in enumerate(contexts, 1):
        title = doc.get('title', f'Oldal {i}')
        # Hosszabb szöveg több kontextusért
        text = doc.get('text', '').strip()[:1200]
        prompt += f"== {title} ==\n{text}\n\n"

    prompt += f"KÉRDÉS: {question}\n\n"
    prompt += "RÉSZLETES VÁLASZ:\n"
    prompt += "(Adj átfogó, informatív választ a wiki tartalmak alapján, "
    prompt += "kiegészítve releváns háttér-információkkal.)\n\n"
    prompt += "Válasz:"

    return prompt
