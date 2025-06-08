#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 11:58:13 2025

@author: zsolt
"""

import pytest
import json
import numpy as np
from pathlib import Path
from unittest import mock
from embedder import Embedder


@pytest.fixture
def dummy_docs():
    return [
        {'text': 'A kutya ugat a holdra.'},
        {'text': 'A macska alszik a napon.'},
        {'text': 'A madarak repülnek az égen.'},
    ]


@pytest.fixture
def embedder_instance():
    return Embedder(model_name='paraphrase-multilingual-MiniLM-L12-v2')


def test_build_index(embedder_instance, dummy_docs):
    embedder_instance.build_index(dummy_docs)
    assert embedder_instance.index.ntotal == len(dummy_docs)
    assert len(embedder_instance.documents) == len(dummy_docs)


def test_query_results(embedder_instance, dummy_docs):
    embedder_instance.build_index(dummy_docs)
    results = embedder_instance.query('Mit csinál a kutya?', top_k=2)
    assert isinstance(results, list)
    assert len(results) <= 2
    for r in results:
        assert 'text' in r


def test_query_empty_index(embedder_instance):
    results = embedder_instance.query('Bármilyen kérdés', top_k=2)
    assert results == []


def test_save_and_load(tmp_path, embedder_instance, dummy_docs):
    embedder_instance.build_index(dummy_docs)

    index_path = tmp_path / 'index.faiss'
    docs_path = tmp_path / 'docs.json'

    embedder_instance.save(index_path, docs_path)

    # új példány
    new_embedder = Embedder()
    new_embedder.load(index_path, docs_path)

    assert new_embedder.index.ntotal == len(dummy_docs)
    assert len(new_embedder.documents) == len(dummy_docs)

    # ellenőrizzük, hogy keresés is működik a betöltött indexszel
    results = new_embedder.query('Hol repül a madár?')
    assert isinstance(results, list)


def test_build_index_with_empty_list(embedder_instance):
    embedder_instance.build_index([])
    assert embedder_instance.index.ntotal == 0
    assert embedder_instance.documents == []


def test_query_invalid_document_index(embedder_instance):
    # Force FAISS index to have more vectors than documents
    docs = [{'text': 'csak egy dokumentum'}]
    embedder_instance.build_index(docs)

    # FAISS indexbe manuálisan rakjunk plusz vektort, ami nem tartozik dokumentumhoz
    extra_vector = np.random.rand(1, 384).astype('float32')
    embedder_instance.index.add(extra_vector)

    # Most 2 vektor van, de csak 1 dokumentum
    results = embedder_instance.query('keresés')
    assert isinstance(results, list)
    assert len(results) >= 1  # Legalább az első valid találat
