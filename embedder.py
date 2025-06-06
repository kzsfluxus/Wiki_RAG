#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:31:49 2025

@author: zsolt
"""

import json
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class Embedder:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.index = faiss.IndexFlatL2(384)
        self.documents = []

    def build_index(self, docs):
        self.documents = docs
        embeddings = self.model.encode([doc['text'] for doc in docs])
        self.index.add(np.array(embeddings).astype('float32'))

    def save(self, index_path='data/index.faiss', docs_path='data/wiki_pages.json'):
        faiss.write_index(self.index, index_path)
        with open(docs_path, 'w', encoding='utf-8') as file:
            json.dump(self.documents, file, ensure_ascii=False, indent=2)

    def load(self, index_path='data/index.faiss', docs_path='data/wiki_pages.json'):
        self.index = faiss.read_index(index_path)
        with open(docs_path, 'r', encoding='utf-8') as file:
            self.documents = json.load(file)

    def query(self, question, top_k=3):
        q_embed = self.model.encode([question]).astype('float32')
        distances, indices = self.index.search(q_embed, top_k)
        return [self.documents[i] for i in indices[0]]
