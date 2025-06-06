#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  6 22:33:15 2025

@author: zsolt
"""

def build_prompt(contexts, question):
    if not contexts:
        return f"Kérdés: {question}\n\nVálasz: Sajnos nincs releváns információ a dokumentumokban."
    
    prompt = "Az alábbi MediaWiki oldalak alapján adj részletes választ a kérdésre.\n"
    prompt += "Használd elsősorban a wiki tartalmakat, de kiegészítheted általános tudásoddal is.\n\n"
    
    prompt += "WIKI FORRÁSOK:\n\n"
    for i, doc in enumerate(contexts, 1):
        title = doc.get('title', f'Oldal {i}')
        text = doc.get('text', '').strip()[:1200]  # Hosszabb szöveg több kontextusért
        prompt += f"== {title} ==\n{text}\n\n"
    
    prompt += f"KÉRDÉS: {question}\n\n"
    prompt += "RÉSZLETES VÁLASZ:\n"
    prompt += "(Adj átfogó, informatív választ a wiki tartalmak alapján, "
    prompt += "kiegészítve releváns háttér-információkkal.)\n\n"
    prompt += "Válasz:"
    
    return prompt