#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:31:49 2025
@author: zsolt
"""
import warnings
import os
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

import json
from pathlib import Path
from retriever import auto_fetch_from_config
from embedder import Embedder
from ollama_runner import run_mistral


WIKI_FILE = 'data/wiki_pages.json'

def load_docs():
    with open(WIKI_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_prompt(contexts, question):
    prompt = "Az alábbi MediaWiki oldalak alapján válaszolj a kérdésre:\n\n"
    for doc in contexts:
        prompt += f"== {doc['title']} ==\n{doc['text'][:1000]}\n\n"
    prompt += f"Kérdés: {question}\nVálasz:"
    return prompt

def main():
    if not Path(WIKI_FILE).exists():
        auto_fetch_from_config()
    
    docs = load_docs()
    embedder = Embedder()
    
    if Path('data/index.faiss').exists():
        embedder.load()
    else:
        embedder.build_index(docs)
        embedder.save()
    
    while True:
        question = input("\n📌 Kérdés (üres = kilépés): ")
        if not question.strip():
            break
        
        results = embedder.query(question)
        prompt = build_prompt(results, question)
        answer = run_mistral(prompt)
        print(f"\n💬 Válasz:\n{answer}\n")

if __name__ == '__main__':
    main()