#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 11:53:33 2025

@author: zsolt
"""

import pytest
from unittest.mock import patch, MagicMock
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

@patch('app.rag_system')
def test_index_get(mock_rag, client):
    mock_rag.is_initialized = True
    response = client.get('/')
    assert response.status_code == 200
    assert b"clean_answer" in response.data or b"Kérlek" in response.data

@patch('app.rag_system')
def test_index_post_valid(mock_rag, client):
    mock_rag.is_initialized = True
    mock_rag.process_question.return_value = "Ez egy válasz."
    response = client.post('/', data={'question': 'Mi az a RAG?'})
    assert response.status_code == 200
    assert b"Ez egy válasz." in response.data

@patch('app.rag_system')
def test_api_ask_success(mock_rag, client):
    mock_rag.is_initialized = True
    mock_rag.process_question.return_value = "API válasz"
    response = client.post('/api/ask', json={'question': 'Teszt kérdés'})
    assert response.status_code == 200
    assert response.get_json()['answer'] == "API válasz"

@patch('app.rag_system')
def test_api_ask_missing_question(mock_rag, client):
    mock_rag.is_initialized = True
    response = client.post('/api/ask', json={})
    assert response.status_code == 400
    assert response.get_json()['error'] == "Nincs kérdés megadva"

@patch('app.rag_system')
def test_refresh_data_success(mock_rag, client):
    mock_rag.refresh_data.return_value = True
    response = client.post('/refresh')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'success'

@patch('app.rag_system')
def test_health_check(mock_rag, client):
    mock_rag.is_initialized = True
    mock_rag.get_system_info.return_value = {"initialized": True}
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'healthy'

@patch('app.rag_system')
def test_system_status(mock_rag, client):
    mock_rag.is_initialized = True
    mock_rag.get_system_info.return_value = {
        "initialized": True,
        "documents_loaded": 5,
        "embedder_ready": True,
        "index_exists": True,
        "wiki_file_exists": True,
        "document_titles": ["Cím 1", "Cím 2"]
    }
    response = client.get('/api/status')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["initialized"] is True
    assert "documents_count" in json_data

def test_404(client):
    response = client.get('/nem_letezik')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Endpoint not found'
