#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:32:30 2025

@author: zsolt
"""

import json
from flask import Flask, request, render_template
from embedder import Embedder
# from retriever import fetch_wiki_pages
from retriever import fetch_related_pages
from ollama_runner import run_mistral
from pathlib import Path

app = Flask(__name__)

WIKI_FILE = 'data/documents.json'

def load_docs():
    with open(WIKI_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def build_prompt(contexts, question):
    prompt = "Az alábbi MediaWiki oldalak alapján válaszolj a kérdésre:\n\n"
    for doc in contexts:
        prompt += f"== {doc['title']} ==\n{doc['text'][:1000]}\n\n"
    prompt += f"Kérdés: {question}\nVálasz:"
    return prompt

@app.route('/', methods=['GET', 'POST'])
def index():
    if not Path(WIKI_FILE).exists():
        #fetch_wiki_pages('hu.wikipedia.org', login_required=False)
        fetch_related_pages('hu.wikipedia.org', 'Budapest', limit=100)
        
    docs = load_docs()
    
    embedder = Embedder()
    if Path('data/index.faiss').exists():
        embedder.load()
    else:
        embedder.build_index(docs)
        embedder.save()
    answer = None
    question = ""
    if request.method == 'POST':
        question = request.form['question']
        results = embedder.query(question)
        prompt = build_prompt(results, question)
        answer = run_mistral(prompt)
    return render_template('index.html', question=question, answer=answer)

if __name__ == '__main__':
    app.run(debug=True)


