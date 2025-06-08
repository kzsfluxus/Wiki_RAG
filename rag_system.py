#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG System - Közös osztály a CLI és Flask alkalmazásokhoz
Created on Thu Jun  6 15:31:49 2025
@author: zsolt
"""
from docs_loader import clear_cache, should_refresh_data, load_docs, WIKI_FILE
from prompt_builder import build_prompt
from text_cleaner import clean_wiki_text
from retriever import auto_fetch_from_config
from ollama_runner import run_ollama_model, stop_ollama_model
from embedder import Embedder
import atexit
import signal
import sys
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class RAGInitializationError(Exception):
    """RAG rendszer inicializálási hiba"""
    pass


class RAGQueryError(Exception):
    """RAG lekérdezési hiba"""
    pass


class RAGSystem:
    """
    Wiki RAG rendszer központi osztálya
    Kezeli az adatok betöltését, indexelését és a kérdések feldolgozását
    """

    def __init__(self):
        self._docs = None
        self._embedder = None
        self._initialized = False
        self._last_config_check = 0
        self._cleanup_registered = False
        self._cleanup_executed = False
        logger.info("🚀 RAG System objektum létrehozva")

        # Cleanup regisztrálása egyszer
        self._register_cleanup()

    def _register_cleanup(self):
        """
        Cleanup funkciók regisztrálása program kilépéskor
        """
        if not self._cleanup_registered:
            # Atexit cleanup regisztrálása
            atexit.register(self._cleanup_handler)

            # Signal handlerek regisztrálása
            try:
                signal.signal(signal.SIGINT, self._signal_handler)   # Ctrl+C
                signal.signal(
                    signal.SIGTERM,
                    self._signal_handler)  # Termination
            except ValueError:
                # Előfordulhat hogy már regisztrálva van vagy nem támogatott
                logger.debug(
                    "Signal handlerek regisztrálása sikertelen (nem kritikus)")

            self._cleanup_registered = True
            logger.debug("🛡️  Cleanup handlerek regisztrálva")

    def _signal_handler(self, signum, frame):
        """Signal handler a program megszakításához"""
        logger.info(f"🛑 Signal fogadva: {signum}")
        self._cleanup_handler()
        sys.exit(0)

    def _cleanup_handler(self):
        """Cleanup handler - ollama processek leállítása"""
        if self._cleanup_executed:  # Dupla futás elkerülése
            return

        self._cleanup_executed = True  # Flag beállítása
        try:
            stop_ollama_model()
        except Exception as e:
            logger.warning(f"⚠️  Cleanup handler hiba: {e}")

    @property
    def is_initialized(self) -> bool:
        """Visszaadja, hogy a rendszer inicializálva van-e"""
        return self._initialized

    def _check_and_refresh_data(self) -> bool:
        """
        Ellenőrzi és frissíti az adatokat ha szükséges

        Returns:
            bool: True ha sikerült, False ha hiba történt
        """
        try:
            if should_refresh_data():
                logger.info("🔄 Adatok frissítése...")
                clear_cache()
                auto_fetch_from_config()

                # Ellenőrizzük, hogy sikerült-e a letöltés
                if not Path(WIKI_FILE).exists():
                    logger.error("❌ Nem sikerült letölteni az adatokat!")
                    return False
            else:
                logger.info("✅ Adatok naprakészek")
            return True
        except Exception as error:
            logger.error(f"❌ Hiba az adatok frissítése során: {error}")
            return False

    def _load_documents(self) -> bool:
        """
        Dokumentumok betöltése

        Returns:
            bool: True ha sikerült, False ha hiba történt
        """
        try:
            self._docs = load_docs()
            logger.info(f"📚 Betöltve: {len(self._docs)} dokumentum")

            # Kiírjuk, hogy milyen oldalakat tartalmaz
            titles = [doc.get('title', 'Névtelen') for doc in self._docs]
            logger.info(
                f"📄 Oldalak: {', '.join(titles[:5])}{'...' if len(titles) > 5 else ''}")
            return True
        except Exception as error:
            logger.error(f"❌ Hiba az adatok betöltése közben: {error}")
            return False

    def _initialize_embedder(self) -> bool:
        """
        Embedder inicializálása és index betöltése/építése

        Returns:
            bool: True ha sikerült, False ha hiba történt
        """
        try:
            self._embedder = Embedder()

            # Index betöltése vagy építése
            if Path('data/index.faiss').exists() and not should_refresh_data():
                logger.info("📊 Index betöltése...")
                self._embedder.load()
            else:
                logger.info("🔨 Index építése...")
                if self._docs is None:
                    logger.error(
                        "❌ Nincs betöltött dokumentum az index építéshez!")
                    return False
                self._embedder.build_index(self._docs)
                self._embedder.save()
                logger.info("✅ Index mentve")
            return True
        except Exception as error:
            logger.error(f"❌ Hiba az embedder inicializálása során: {error}")
            return False

    def initialize(self) -> bool:
        """
        Teljes rendszer inicializálása

        Returns:
            bool: True ha sikerült, False ha hiba történt

        Raises:
            RAGInitializationError: Ha kritikus hiba történt
        """
        try:
            logger.info("🚀 RAG rendszer inicializálása...")

            # Adatok ellenőrzése és frissítése
            if not self._check_and_refresh_data():
                raise RAGInitializationError("Adatok frissítése sikertelen")

            # Dokumentumok betöltése
            if not self._load_documents():
                raise RAGInitializationError(
                    "Dokumentumok betöltése sikertelen")

            # Embedder inicializálása
            if not self._initialize_embedder():
                raise RAGInitializationError(
                    "Embedder inicializálása sikertelen")

            self._initialized = True
            logger.info("🎯 RAG rendszer kész!")
            return True

        except RAGInitializationError:
            raise
        except Exception as error:
            logger.error(f"❌ Váratlan hiba az inicializálás során: {error}")
            raise RAGInitializationError(f"Inicializálási hiba: {str(error)}")

    def refresh_data(self) -> bool:
        """
        Manuális adatfrissítés és újrainicializálás

        Returns:
            bool: True ha sikerült, False ha hiba történt
        """
        try:
            logger.info("🔄 Manuális adatfrissítés...")

            # Cache törlése
            clear_cache()

            # Reinicializálás
            self._initialized = False
            self._docs = None
            self._embedder = None

            return self.initialize()

        except Exception as error:
            logger.error(f"❌ Hiba az adatfrissítés során: {error}")
            return False

    def process_question(self, question: str) -> str:
        """
        Kérdés feldolgozása és válasz generálása

        Args:
            question (str): A felhasználó kérdése

        Returns:
            str: A tisztított válasz

        Raises:
            RAGQueryError: Ha hiba történt a feldolgozás során
        """
        if not self._initialized:
            raise RAGQueryError("A RAG rendszer nincs inicializálva!")

        if not question or not question.strip():
            return "Kérlek, adj meg egy kérdést!"

        try:
            question = question.strip()
            logger.info(f"🔍 Kérdés feldolgozása: {question[:50]}...")

            # Releváns dokumentumok keresése
            results = self._embedder.query(question)
            logger.debug(f"📊 Találat: {len(results)} dokumentum")

            # Prompt építése és válasz generálása
            logger.info("🤖 Válasz generálása...")
            prompt = build_prompt(results, question)
            raw_answer = run_ollama_model(prompt)

            # Válasz tisztítása
            clean_answer = clean_wiki_text(raw_answer)
            logger.info(f"✅ Válasz generálva: {len(clean_answer)} karakter")

            return clean_answer

        except Exception as error:
            logger.error(f"❌ Hiba a kérdés feldolgozása során: {error}")
            raise RAGQueryError(f"Kérdés feldolgozási hiba: {str(error)}")

    def get_system_info(self) -> Dict[str, Any]:
        """
        Rendszer információk lekérdezése

        Returns:
            Dict[str, Any]: Rendszer állapot információk
        """
        info = {
            "initialized": self._initialized,
            "documents_loaded": len(self._docs) if self._docs else 0,
            "embedder_ready": self._embedder is not None,
            "index_exists": Path('data/index.faiss').exists(),
            "wiki_file_exists": Path(WIKI_FILE).exists(),
            "cleanup_registered": self._cleanup_registered
        }

        if self._docs:
            info["document_titles"] = [
                doc.get('title', 'Névtelen') for doc in self._docs]

        return info

    def __enter__(self):
        """Context manager support"""
        if not self._initialized:
            self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        logger.info("🧹 RAG System context manager cleanup...")
        self._cleanup_handler()
