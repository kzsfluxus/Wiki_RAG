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

from flask import Flask, request, render_template
from pathlib import Path
import json
from embedder import Embedder
from ollama_runner import run_mistral
from retriever import auto_fetch_from_config


app = Flask(__name__)
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if not Path(WIKI_FILE).exists():
        auto_fetch_from_config()

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
