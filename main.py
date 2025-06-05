#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:31:10 2025

@author: zsolt
"""

import json
from embedder import Embedder
from retriever import fetch_wiki_pages
from ollama_runner import run_mistral
from pathlib import Path

WIKI_FILE = 'data/documents.json'

def load_docs():
    with open(WIKI_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_prompt(contexts, question):
    prompt = "Az alábbi MediaWiki oldalak alapján válaszolj a kérdésre:\n\n"
    for doc in contexts:
        prompt += f"== {doc['title']} ==\n{doc['text'][:1000]}\n\n"  # vágás, ha hosszú
    prompt += f"\nKérdés: {question}\nVálasz:"
    return prompt

def main():
    if not Path(WIKI_FILE).exists():
        fetch_wiki_pages('hu.wikipedia.org', login_required=False)

    docs = load_docs()

    embedder = Embedder()
    if Path('data/index.faiss').exists():
        embedder.load()
    else:
        embedder.build_index(docs)
        embedder.save()


    while True:
        question = input("❓ Kérdés (ENTER kilép): ")
        if not question.strip():
            break

        contexts = embedder.query(question, top_k=3)
        prompt = build_prompt(contexts, question)
        answer = run_mistral(prompt)
        print("\n🧠 Válasz:")
        print(answer)

if __name__ == '__main__':
    main()
