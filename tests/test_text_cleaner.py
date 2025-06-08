#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 11:51:15 2025

@author: zsolt
"""

import pytest
from text_cleaner import clean_wiki_text

def test_empty_input():
    assert clean_wiki_text("") == ""
    assert clean_wiki_text(None) is None

def test_basic_html_removal():
    text = "Ez egy <b>HTML</b> taggel."
    cleaned = clean_wiki_text(text)
    assert cleaned == "Ez egy HTML taggel."

def test_wiki_link_removal():
    text = "Ez egy [[Belso link]] teszt."
    cleaned = clean_wiki_text(text)
    assert cleaned == "Ez egy Belso link teszt."

def test_wiki_display_link():
    text = "Ez egy [[link|megjelenített szöveg]] teszt."
    cleaned = clean_wiki_text(text)
    assert cleaned == "Ez egy megjelenített szöveg teszt."

def test_template_removal():
    text = "Ez egy {{Sablon}} szöveg."
    cleaned = clean_wiki_text(text)
    assert cleaned == "Ez egy szöveg."

def test_reference_removal():
    text = "Ez egy mondat.<ref>Forrás</ref> Vége."
    cleaned = clean_wiki_text(text)
    assert cleaned == "Ez egy mondat. Vége."

def test_self_closing_reference():
    text = "Valami szöveg <ref name=\"a\"/> folytatás."
    cleaned = clean_wiki_text(text)
    assert cleaned == "Valami szöveg folytatás."

def test_formatting_removal():
    text = "Ez egy '''félkövér''' és ''dőlt'' szöveg."
    cleaned = clean_wiki_text(text)
    assert cleaned == "Ez egy félkövér és dőlt szöveg."

def test_whitespace_cleanup():
    text = "Ez  egy     szöveg.\n \n\n\nMásik\n  sor."
    cleaned = clean_wiki_text(text)
    assert cleaned == "Ez egy szöveg.\n\nMásik\nsor."
