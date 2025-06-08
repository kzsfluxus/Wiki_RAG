#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:31:49 2025
@author: zsolt

Embedder modul dokumentum vektorok kezelésére és keresésére.
"""
import os
os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import logging
import json
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)

class Embedder:
    """
    Dokumentum embedder osztály FAISS indexszel és sentence transformerrel.

    Ez az osztály dokumentumok vektorizálására, indexelésére és keresésére szolgál.
    Használja a sentence-transformers könyvtárat a szövegek embedding-jéhez és
    a FAISS-t a gyors hasonlósági kereséshez.

    Attributes:
        model (SentenceTransformer): A sentence transformer modell.
        index (faiss.Index): A FAISS index a vektorok tárolására.
        documents (list): A dokumentumok listája.
    """

    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Embedder osztály inicializálása.

        Args:
            model_name (str, optional): A használandó sentence transformer modell neve.
                Alapértelmezett: 'paraphrase-multilingual-MiniLM-L12-v2'
        """
        self.model = SentenceTransformer(model_name)
        self.index = faiss.IndexFlatL2(384)
        self.documents = []
        logger.info("Embedder inicializálva - model: %s", model_name)

    def build_index(self, docs):
        """
        FAISS index építése a megadott dokumentumokból.

        Minden dokumentumhoz embedding-et készít és hozzáadja a FAISS indexhez.

        Args:
            docs (list): Dokumentumok listája, ahol minden elem egy dict 'text' kulccsal.

        Raises:
            ValueError: Ha a dokumentumok listája üres vagy nem megfelelő formátumú.
        """
        logger.info("Index építése: %d dokumentum", len(docs))
        self.documents = docs

        if not docs:
            logger.warning("Nincs dokumentum az indexeléshez!")
            return

        # Debug: első dokumentum ellenőrzése
        first_doc_text = docs[0].get('text', 'NINCS TEXT MEZŐ')
        logger.debug("Első dokumentum: %s...", first_doc_text[:100])

        embeddings = self.model.encode(
            [doc['text'] for doc in docs], show_progress_bar=False)

        logger.debug("Embedding méret: %s", embeddings.shape)

        self.index.add(np.array(embeddings).astype('float32'))

        logger.info("Index kész: %d vektor", self.index.ntotal)

    def save(self, index_path=Path('data/index.faiss'),
             docs_path=Path('data/wiki_pages.json')):
        """
        Index és dokumentumok mentése fájlokba.

        Args:
            index_path (Path, optional): A FAISS index mentési útvonala.
                Alapértelmezett: Path('data/index.faiss')
            docs_path (Path, optional): A dokumentumok JSON fájljának mentési útvonala.
                Alapértelmezett: Path('data/wiki_pages.json')

        Raises:
            Exception: Ha hiba történik a mentés során.
        """
        try:
            # Biztosítjuk, hogy a könyvtár létezik
            index_path.parent.mkdir(parents=True, exist_ok=True)
            docs_path.parent.mkdir(parents=True, exist_ok=True)

            # Index mentése
            faiss.write_index(self.index, str(index_path))

            # Dokumentumok mentése
            with docs_path.open('w', encoding='utf-8') as file:
                json.dump(self.documents, file, ensure_ascii=False, indent=2)

            logger.info("Index mentve: %d dokumentum, fájlok: %s, %s",
                        len(self.documents), index_path, docs_path)
        except Exception as error:
            logger.error("Hiba index mentése közben: %s", error)
            raise

    def load(self, index_path=Path('data/index.faiss'),
             docs_path=Path('data/wiki_pages.json')):
        """
        Index és dokumentumok betöltése fájlokból.

        Args:
            index_path (Path, optional): A FAISS index fájl útvonala.
                Alapértelmezett: Path('data/index.faiss')
            docs_path (Path, optional): A dokumentumok JSON fájljának útvonala.
                Alapértelmezett: Path('data/wiki_pages.json')

        Raises:
            FileNotFoundError: Ha a fájlok nem találhatók.
            Exception: Ha egyéb hiba történik a betöltés során.
        """
        try:
            # Index betöltése
            self.index = faiss.read_index(str(index_path))

            # Dokumentumok betöltése
            with docs_path.open('r', encoding='utf-8') as file:
                self.documents = json.load(file)

            logger.info("Index betöltve: %d dokumentum, %d vektor",
                        len(self.documents), self.index.ntotal)

        except FileNotFoundError as error:
            logger.error("Index fájl nem található: %s", error)
            raise
        except Exception as error:
            logger.error("Index betöltési hiba: %s", error)
            raise

    def query(self, question, top_k=3):
        """
        Keresés a dokumentumok között egy kérdés alapján.

        A kérdéshez embedding-et készít és megkeresi a legközelebbi dokumentumokat
        a FAISS indexben.

        Args:
            question (str): A keresendő kérdés vagy szöveg.
            top_k (int, optional): A visszaadandó dokumentumok száma.
                Alapértelmezett: 3

        Returns:
            list: A legközelebbi dokumentumok listája, üres lista hiba esetén.

        Raises:
            Exception: Ha hiba történik a keresés során (logolva, de nem dobva).
        """
        logger.debug(
            "Keresés indítása - kérdés: '%s', top_k: %d",
            question,
            top_k)

        # Ellenőrzések
        if self.index.ntotal == 0:
            logger.warning("Üres index!")
            return []

        if not self.documents:
            logger.warning("Nincs dokumentum!")
            return []

        # Keresés
        try:
            q_embed = self.model.encode([question],
                                        show_progress_bar=False).astype('float32')
            distances, indices = self.index.search(q_embed, top_k)

            logger.debug("Keresési eredmények - távolságok: %s", distances[0])
            logger.debug("Keresési eredmények - indexek: %s", indices[0])

            # Biztonságos dokumentum lekérés
            results = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(self.documents):
                    doc = self.documents[idx]
                    doc_preview = doc.get('text', '')[:100]
                    logger.debug("Találat %d (távolság: %.3f): %s...",
                                 i + 1, distances[0][i], doc_preview)
                    results.append(doc)
                else:
                    logger.warning("Érvénytelen index: %d", idx)

            logger.info("Keresés befejezve - %d találat", len(results))
            return results

        except Exception as error:
            logger.error("Hiba keresés közben: %s", error)
            return []
