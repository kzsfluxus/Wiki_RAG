#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 12:08:13 2025

@author: zsolt
"""

import pytest
from unittest.mock import patch, MagicMock
from rag_system import RAGSystem, RAGInitializationError, RAGQueryError


@pytest.fixture
def rag():
    return RAGSystem()


@patch("rag_system.should_refresh_data", return_value=False)
@patch("rag_system.Path.exists", return_value=True)
@patch("rag_system.load_docs", return_value=[{"title": "Teszt oldal", "text": "Ez egy teszt szöveg"}])
@patch("rag_system.Embedder")
def test_initialize_success(mock_embedder_class, mock_load_docs, mock_exists, mock_refresh, rag):
    mock_embedder = MagicMock()
    mock_embedder_class.return_value = mock_embedder
    mock_embedder.load.return_value = None
    assert rag.initialize() is True
    assert rag.is_initialized is True


def test_process_question_without_init(rag):
    with pytest.raises(RAGQueryError):
        rag.process_question("Mi Magyarország fővárosa?")


@patch("rag_system.should_refresh_data", return_value=False)
@patch("rag_system.Path.exists", return_value=True)
@patch("rag_system.load_docs", return_value=[{"title": "Teszt oldal", "text": "Ez egy teszt szöveg"}])
@patch("rag_system.Embedder")
@patch("rag_system.build_prompt", return_value="KONTEKSTUS + KÉRDÉS")
@patch("rag_system.run_ollama_model", return_value="Budapest.")
@patch("rag_system.clean_wiki_text", return_value="Budapest")
def test_process_question_success(
    mock_clean, mock_run, mock_prompt, mock_embedder_class, mock_load_docs, mock_exists, mock_refresh, rag
):
    mock_embedder = MagicMock()
    mock_embedder.query.return_value = [{"title": "Teszt", "text": "Budapest a főváros"}]
    mock_embedder.build_index.return_value = None
    mock_embedder.save.return_value = None
    mock_embedder_class.return_value = mock_embedder

    rag.initialize()
    response = rag.process_question("Mi Magyarország fővárosa?")
    assert response == "Budapest"


def test_get_system_info_uninitialized(rag):
    info = rag.get_system_info()
    assert info["initialized"] is False
    assert info["documents_loaded"] == 0
    assert info["embedder_ready"] is False
