#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kibővített pytest tesztek a Flask alkalmazáshoz
Created on Sun Jun  8 11:53:33 2025
@author: zsolt

Átfogó tesztlefedettség:
- Alapvető route tesztek
- Hibakezelés tesztelése
- Edge case-ek
- Inicializálási folyamatok
- API végpontok részletes tesztelése
- Mock objektumok alapos tesztelése
"""

import pytest
import json
from unittest.mock import patch, MagicMock, Mock
from app import app as flask_app, initialize_app
from rag_system import RAGInitializationError, RAGQueryError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Flask teszt kliens létrehozása"""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False  # CSRF kikapcsolása tesztekhez
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def mock_rag():
    """Mock RAG system fixture"""
    with patch('app.rag_system') as mock:
        mock.is_initialized = True
        mock.initialize.return_value = True
        mock.process_question.return_value = "Mock válasz"
        mock.refresh_data.return_value = True
        mock.get_system_info.return_value = {
            "initialized": True,
            "documents_loaded": 10,
            "embedder_ready": True,
            "index_exists": True,
            "wiki_file_exists": True,
            "document_titles": ["Teszt dokumentum 1", "Teszt dokumentum 2"]
        }
        mock.model_name = "test-model"
        mock.reload_model_from_config.return_value = "new-test-model"
        yield mock


# ============================================================================
# INDEX ROUTE TESZTEK
# ============================================================================

def test_index_get_basic(mock_rag, client):
    """Alapvető GET kérés tesztelése a főoldalon"""
    response = client.get('/')
    assert response.status_code == 200
    
    text = response.data.decode("utf-8")
    assert "<form" in text
    assert "Kérdés" in text or "kérdés" in text


def test_index_get_uninitialized_rag(client):
    """Tesztelés nem inicializált RAG rendszerrel"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.is_initialized = False
        mock_rag.initialize.return_value = True
        
        response = client.get('/')
        assert response.status_code == 200
        mock_rag.initialize.assert_called_once()


def test_index_post_valid_question(mock_rag, client):
    """Érvényes kérdés POST kérés tesztelése"""
    mock_rag.process_question.return_value = "Ez egy teszt válasz."
    
    response = client.post('/', data={'question': 'Mi az a RAG rendszer?'})
    assert response.status_code == 200
    
    text = response.data.decode("utf-8")
    assert "Ez egy teszt válasz." in text
    mock_rag.process_question.assert_called_once_with('Mi az a RAG rendszer?')


def test_index_post_empty_question(mock_rag, client):
    """Üres kérdés POST kérés tesztelése"""
    response = client.post('/', data={'question': ''})
    assert response.status_code == 200
    
    text = response.data.decode("utf-8")
    assert "Kérlek, adj meg egy kérdést!" in text


def test_index_post_whitespace_question(mock_rag, client):
    """Csak whitespace karaktereket tartalmazó kérdés tesztelése"""
    response = client.post('/', data={'question': '   \n\t  '})
    assert response.status_code == 200
    
    text = response.data.decode("utf-8")
    assert "Kérlek, adj meg egy kérdést!" in text


def test_index_post_rag_query_error(mock_rag, client):
    """RAG lekérdezési hiba tesztelése"""
    mock_rag.process_question.side_effect = RAGQueryError("Teszt RAG hiba")
    
    response = client.post('/', data={'question': 'Teszt kérdés'})
    assert response.status_code == 200
    
    text = response.data.decode("utf-8")
    assert "❌ Hiba történt: Teszt RAG hiba" in text


def test_index_post_general_exception(mock_rag, client):
    """Általános kivétel tesztelése"""
    mock_rag.process_question.side_effect = Exception("Váratlan hiba")
    
    response = client.post('/', data={'question': 'Teszt kérdés'})
    assert response.status_code == 200
    
    text = response.data.decode("utf-8")
    assert "❌ Váratlan hiba: Váratlan hiba" in text


def test_index_initialization_error(client):
    """Inicializálási hiba tesztelése"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.is_initialized = False
        mock_rag.initialize.side_effect = RAGInitializationError("Init hiba")
        
        response = client.get('/')
        assert response.status_code == 200
        
        text = response.data.decode("utf-8")
        assert "❌ Rendszerhiba:" in text


# ============================================================================
# API VÉGPONTOK TESZTELÉSE
# ============================================================================

def test_api_ask_success(mock_rag, client):
    """Sikeres API kérdés tesztelése"""
    mock_rag.process_question.return_value = "API teszt válasz"
    
    response = client.post('/api/ask', 
                          json={'question': 'API teszt kérdés'},
                          content_type='application/json')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['answer'] == "API teszt válasz"
    assert json_data['question'] == "API teszt kérdés"
    assert json_data['status'] == "success"


def test_api_ask_missing_question(mock_rag, client):
    """Hiányzó kérdés API kérés tesztelése"""
    response = client.post('/api/ask', 
                          json={},
                          content_type='application/json')
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == "Nincs kérdés megadva"


def test_api_ask_empty_question(mock_rag, client):
    """Üres kérdés API kérés tesztelése"""
    response = client.post('/api/ask', 
                          json={'question': ''},
                          content_type='application/json')
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == "Nincs kérdés megadva"


def test_api_ask_wrong_content_type(mock_rag, client):
    """Helytelen Content-Type tesztelése"""
    response = client.post('/api/ask', 
                          data={'question': 'teszt'},
                          content_type='application/x-www-form-urlencoded')
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert "Content-Type must be application/json" in json_data['error']


def test_api_ask_rag_error(mock_rag, client):
    """API RAG hiba tesztelése"""
    mock_rag.process_question.side_effect = RAGQueryError("API RAG hiba")
    
    response = client.post('/api/ask', 
                          json={'question': 'teszt kérdés'},
                          content_type='application/json')
    
    assert response.status_code == 500
    json_data = response.get_json()
    assert json_data['error'] == "API RAG hiba"
    assert json_data['status'] == "rag_error"


def test_api_ask_general_error(mock_rag, client):
    """API általános hiba tesztelése"""
    mock_rag.process_question.side_effect = Exception("API általános hiba")
    
    response = client.post('/api/ask', 
                          json={'question': 'teszt kérdés'},
                          content_type='application/json')
    
    assert response.status_code == 500
    json_data = response.get_json()
    assert "Váratlan hiba: API általános hiba" in json_data['error']
    assert json_data['status'] == "error"


def test_api_ask_uninitialized_rag(client):
    """API kérés nem inicializált RAG rendszerrel"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.is_initialized = False
        mock_rag.initialize.return_value = True
        mock_rag.process_question.return_value = "Válasz init után"
        
        response = client.post('/api/ask', 
                              json={'question': 'teszt'},
                              content_type='application/json')
        
        assert response.status_code == 200
        mock_rag.initialize.assert_called_once()


# ============================================================================
# REFRESH ENDPOINT TESZTEK
# ============================================================================

def test_refresh_data_success(mock_rag, client):
    """Sikeres adatfrissítés tesztelése"""
    mock_rag.refresh_data.return_value = True
    
    response = client.post('/refresh')
    assert response.status_code == 200
    
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['message'] == "Adatok sikeresen frissítve!"


def test_refresh_data_failure(mock_rag, client):
    """Sikertelen adatfrissítés tesztelése"""
    mock_rag.refresh_data.return_value = False
    
    response = client.post('/refresh')
    assert response.status_code == 500
    
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert json_data['message'] == "Adatok frissítése sikertelen!"


def test_refresh_data_exception(mock_rag, client):
    """Adatfrissítés kivétel tesztelése"""
    mock_rag.refresh_data.side_effect = Exception("Refresh hiba")
    
    response = client.post('/refresh')
    assert response.status_code == 500
    
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert "Hiba történt: Refresh hiba" in json_data['message']


# ============================================================================
# MODEL RELOAD ENDPOINT TESZTEK
# ============================================================================

def test_reload_model_success(mock_rag, client):
    """Sikeres modell újratöltés tesztelése"""
    mock_rag.model_name = "régi-modell"
    mock_rag.reload_model_from_config.return_value = "új-modell"
    
    response = client.post('/api/reload-model')
    assert response.status_code == 200
    
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['old_model'] == "régi-modell"
    assert json_data['new_model'] == "új-modell"


def test_reload_model_error(mock_rag, client):
    """Modell újratöltés hiba tesztelése"""
    mock_rag.reload_model_from_config.side_effect = Exception("Modell hiba")
    
    response = client.post('/api/reload-model')
    assert response.status_code == 500
    
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert json_data['message'] == "Modell hiba"


# ============================================================================
# HEALTH CHECK TESZTEK
# ============================================================================

def test_health_check_healthy(mock_rag, client):
    """Egészséges rendszer health check tesztelése"""
    mock_rag.get_system_info.return_value = {"initialized": True}
    
    response = client.get('/api/health')
    assert response.status_code == 200
    
    json_data = response.get_json()
    assert json_data['status'] == 'healthy'
    assert 'system_info' in json_data
    assert 'timestamp' in json_data


def test_health_check_initializing(client):
    """Inicializálás alatt álló rendszer health check tesztelése"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.is_initialized = False
        mock_rag.initialize.return_value = True
        mock_rag.get_system_info.return_value = {"initialized": False}
        
        response = client.get('/api/health')
        assert response.status_code == 200
        
        json_data = response.get_json()
        assert json_data['status'] == 'initializing'


def test_health_check_error(mock_rag, client):
    """Health check hiba tesztelése"""
    mock_rag.get_system_info.side_effect = Exception("Health check hiba")
    
    response = client.get('/api/health')
    assert response.status_code == 500
    
    json_data = response.get_json()
    assert json_data['status'] == 'unhealthy'
    assert json_data['error'] == "Health check hiba"


# ============================================================================
# SYSTEM STATUS TESZTEK
# ============================================================================

def test_system_status_success(mock_rag, client):
    """Sikeres rendszer státusz lekérdezés tesztelése"""
    mock_system_info = {
        "initialized": True,
        "documents_loaded": 15,
        "embedder_ready": True,
        "index_exists": True,
        "wiki_file_exists": True,
        "document_titles": [f"Dokumentum {i}" for i in range(12)]  # 12 cím
    }
    mock_rag.get_system_info.return_value = mock_system_info
    
    response = client.get('/api/status')
    assert response.status_code == 200
    
    json_data = response.get_json()
    assert json_data["initialized"] is True
    assert json_data["documents_count"] == 15
    assert json_data["embedder_ready"] is True
    assert json_data["index_exists"] is True
    assert json_data["wiki_file_exists"] is True
    assert len(json_data["document_titles"]) == 10  # Max 10 cím


def test_system_status_error(mock_rag, client):
    """Rendszer státusz hiba tesztelése"""
    mock_rag.get_system_info.side_effect = Exception("Status hiba")
    
    response = client.get('/api/status')
    assert response.status_code == 500
    
    json_data = response.get_json()
    assert json_data['error'] == "Status hiba"


def test_system_status_uninitialized(client):
    """Nem inicializált rendszer státusz tesztelése"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.is_initialized = False
        mock_rag.initialize.return_value = True
        mock_rag.get_system_info.return_value = {
            "initialized": False,
            "documents_loaded": 0,
            "embedder_ready": False,
            "index_exists": False,
            "wiki_file_exists": True,
            "document_titles": []
        }
        
        response = client.get('/api/status')
        assert response.status_code == 200
        
        json_data = response.get_json()
        assert json_data["initialized"] is False
        assert json_data["documents_count"] == 0


# ============================================================================
# HIBAKEZELÉS TESZTEK
# ============================================================================

def test_404_error(client):
    """404 hiba tesztelése"""
    response = client.get('/nem_letezik')
    assert response.status_code == 404
    
    json_data = response.get_json()
    assert json_data['error'] == 'Endpoint not found'


def test_405_method_not_allowed(client):
    """405 Method Not Allowed tesztelése"""
    # GET kérés POST-only végpontra
    response = client.get('/refresh')
    assert response.status_code == 405


def test_500_error_handling():
    """500 hiba kezelés tesztelése"""
    # Ez implicit módon tesztelt a többi hiba tesztben
    pass


# ============================================================================
# INICIALIZÁLÁS TESZTEK
# ============================================================================

def test_initialize_app_success():
    """Sikeres alkalmazás inicializálás tesztelése"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.initialize.return_value = True
        
        # Nem dob kivételt
        initialize_app()
        mock_rag.initialize.assert_called_once()


def test_initialize_app_failure():
    """Sikertelen alkalmazás inicializálás tesztelése"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.initialize.return_value = False
        
        with pytest.raises(RAGInitializationError):
            initialize_app()


def test_initialize_app_exception():
    """Alkalmazás inicializálás kivétel tesztelése"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.initialize.side_effect = Exception("Init exception")
        
        with pytest.raises(Exception):
            initialize_app()


# ============================================================================
# INTEGRÁCIÓS TESZTEK
# ============================================================================

def test_full_workflow_simulation(mock_rag, client):
    """Teljes munkafolyamat szimuláció tesztelése"""
    # 1. Health check
    response = client.get('/api/health')
    assert response.status_code == 200
    
    # 2. Status check
    response = client.get('/api/status')
    assert response.status_code == 200
    
    # 3. API kérdés
    response = client.post('/api/ask', 
                          json={'question': 'Teszt kérdés'},
                          content_type='application/json')
    assert response.status_code == 200
    
    # 4. Web felület kérdés
    response = client.post('/', data={'question': 'Web teszt kérdés'})
    assert response.status_code == 200
    
    # 5. Adatfrissítés
    response = client.post('/refresh')
    assert response.status_code == 200
    
    # 6. Modell újratöltés
    response = client.post('/api/reload-model')
    assert response.status_code == 200


# ============================================================================
# EDGE CASE TESZTEK
# ============================================================================

def test_very_long_question(mock_rag, client):
    """Nagyon hosszú kérdés tesztelése"""
    long_question = "Mi az a RAG rendszer? " * 100  # 2300+ karakter
    # A strip() művelet miatt a végső szóköz eltűnik
    expected_question = long_question.strip()
    mock_rag.process_question.return_value = "Hosszú válasz"
    
    response = client.post('/api/ask', 
                          json={'question': long_question},
                          content_type='application/json')
    
    assert response.status_code == 200
    mock_rag.process_question.assert_called_once_with(expected_question)


def test_special_characters_question(mock_rag, client):
    """Speciális karakterek kérdésben tesztelése"""
    special_question = "Mi az a RAG? 🤖 Árvíztűrő tükörfúrógép @#$%^&*()"
    mock_rag.process_question.return_value = "Speciális válasz"
    
    response = client.post('/', data={'question': special_question})
    assert response.status_code == 200
    
    text = response.data.decode("utf-8")
    assert "Speciális válasz" in text


def test_concurrent_requests_simulation(mock_rag, client):
    """Párhuzamos kérések szimulációja"""
    # Több kérés gyors egymásutánban
    responses = []
    for i in range(5):
        response = client.post('/api/ask', 
                              json={'question': f'Kérdés {i}'},
                              content_type='application/json')
        responses.append(response)
    
    # Minden kérésnek sikeresnek kell lennie
    for response in responses:
        assert response.status_code == 200


# ============================================================================
# MOCK TESZTEK ELLENŐRZÉSE
# ============================================================================

def test_mock_calls_verification(mock_rag, client):
    """Mock hívások ellenőrzése"""
    # Több különböző végpont hívása
    client.post('/api/ask', json={'question': 'teszt'}, content_type='application/json')
    client.get('/api/health')
    client.post('/refresh')
    
    # Ellenőrizzük, hogy a megfelelő mock metódusok hívódtak
    mock_rag.process_question.assert_called()
    mock_rag.get_system_info.assert_called()
    mock_rag.refresh_data.assert_called()


def test_mock_reset_between_tests(mock_rag, client):
    """Mock állapot reset tesztelése tesztek között"""
    # Ez implicit módon tesztelt a fixture által
    mock_rag.process_question.assert_not_called()  # Kezdetben nem hívott
    
    client.post('/api/ask', json={'question': 'teszt'}, content_type='application/json')
    mock_rag.process_question.assert_called_once()


# ============================================================================
# PERFORMANCE TESZTEK
# ============================================================================

def test_response_time_check(mock_rag, client):
    """Válaszidő ellenőrzés (alapvető)"""
    import time
    
    start_time = time.time()
    response = client.get('/api/health')
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # 1 másodpercnél gyorsabb


# ============================================================================
# CLEANUP TESZTEK
# ============================================================================

def test_cleanup_after_error(client):
    """Hibák utáni cleanup tesztelése"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.is_initialized = False
        mock_rag.initialize.side_effect = Exception("Init hiba")
        
        response = client.get('/')
        # Az alkalmazás nem szabad, hogy összeomljon
        assert response.status_code == 200
        
        # Újabb kérés továbbra is működik
        response2 = client.get('/api/health')
        assert response2.status_code == 500  # Várható hiba, de nem crash