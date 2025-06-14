#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 12:12:09 2025

@author: zsolt
"""

import pytest
from prompt_builder import build_prompt


def test_build_prompt_with_contexts():
    contexts = [
        {'title': 'Python', 'text': 'Python egy programozási nyelv, amelyet Guido van Rossum fejlesztett ki.'}
    ]
    question = "Mi a Python?"
    prompt = build_prompt(contexts, question)

    assert "== Python ==" in prompt
    assert "KÉRDÉS: Mi a Python?" in prompt
    assert "RÉSZLETES VÁLASZ:" in prompt
    assert prompt.startswith("Az alábbi MediaWiki-oldalak alapján válaszolj a kérdésre")


def test_build_prompt_with_empty_context():
    contexts = []
    question = "Mi a fővárosa Franciaországnak?"
    prompt = build_prompt(contexts, question)

    assert "nincs releváns információ" in prompt
    assert question in prompt


def test_truncate_long_text():
    long_text = "A" * 2000  # 2000 karakter hosszú
    contexts = [{'title': 'Hosszú szöveg', 'text': long_text}]
    question = "Mi ez a szöveg?"
    prompt = build_prompt(contexts, question)

    assert "== Hosszú szöveg ==" in prompt
    assert len(prompt) < 2500  # promptban csak 1200 karakter lehet a szövegből, plusz keretek


def test_build_prompt_missing_title():
    contexts = [{'text': 'Ez egy névtelen oldal szövege.'}]
    question = "Mi ez?"
    prompt = build_prompt(contexts, question)

    assert "== Oldal 1 ==" in prompt
    assert "Ez egy névtelen oldal szövege." in prompt
