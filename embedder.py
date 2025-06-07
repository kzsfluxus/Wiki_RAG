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
import logging

logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        self.model = SentenceTransformer(model_name)
        self.index = faiss.IndexFlatL2(384)
        self.documents = []
    
    def build_index(self, docs):
        print(f"📊 Index építése: {len(docs)} dokumentum")
        self.documents = docs
        if not docs:
            print("⚠️ Nincs dokumentum az indexeléshez!")
            return
        
        # Debug: első dokumentum ellenőrzése
        print(f"📄 Első dokumentum: {docs[0].get('text', 'NINCS TEXT MEZŐ')[:100]}...")
        
        embeddings = self.model.encode([doc['text'] for doc in docs], show_progress_bar=False)
        print(f"🔢 Embedding méret: {embeddings.shape}")
        
        self.index.add(np.array(embeddings).astype('float32'))
        print(f"✅ Index kész: {self.index.ntotal} vektor")
    
    def save(self, index_path='data/index.faiss', docs_path='data/wiki_pages.json'):
        faiss.write_index(self.index, index_path)
        with open(docs_path, 'w', encoding='utf-8') as file:
            json.dump(self.documents, file, ensure_ascii=False, indent=2)
        print(f"💾 Mentve: {len(self.documents)} dokumentum")
    
    def load(self, index_path='data/index.faiss', docs_path='data/wiki_pages.json'):
        try:
            self.index = faiss.read_index(index_path)
            with open(docs_path, 'r', encoding='utf-8') as file:
                self.documents = json.load(file)
            print(f"📂 Betöltve: {len(self.documents)} dokumentum, {self.index.ntotal} vektor")
        except FileNotFoundError as e:
            print(f"❌ Fájl nem található: {e}")
        except Exception as e:
            print(f"❌ Betöltési hiba: {e}")
    
    def query(self, question, top_k=3):
        print(f"🔍 Keresés: '{question}' (top_k={top_k})")
        
        # Ellenőrzések
        if self.index.ntotal == 0:
            print("⚠️ Üres index!")
            return []
        
        if not self.documents:
            print("⚠️ Nincs dokumentum!")
            return []
        
        # Keresés
        q_embed = self.model.encode([question], show_progress_bar=False).astype('float32')
        distances, indices = self.index.search(q_embed, top_k)
        
        logger.debug(f"📏 Távolságok: {distances[0]}")
        logger.debug(f"📍 Indexek: {indices[0]}")
        
        # Biztonságos dokumentum lekérés
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.documents):  # Érvényes index ellenőrzés
                doc = self.documents[idx]
                logger.debug(f"📄 {i+1}. találat (távolság: {distances[0][i]:.3f}): {doc.get('text', '')[:100]}...")
                results.append(doc)
            else:
                print(f"⚠️ Érvénytelen index: {idx}")
        
        return results
